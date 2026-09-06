from pathlib import Path
from typing import Optional, List, Dict, Any

from src.profiles.schemas import EmployeeCreate, EmployeeUpdate, EmployeeItem
from src.profiles.repository import ProfileRepository
from src.utils.logging import app_logger


class EmployeeService:
    """
    Business Service Layer for Employee Management.
    """

    def __init__(self, repository: Optional[ProfileRepository] = None, db_path: Optional[Path] = None):
        self.repository = repository or ProfileRepository(db_path=db_path)

    def list_employees(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Lists all registered employees."""
        return self.repository.get_all_employees(active_only=active_only)

    def get_employee(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Looks up an employee by integer ID or employee code (e.g. EMP001).
        This dual resolution ensures Phase 4 Face Recognition can immediately query by code.
        """
        if identifier.isdigit():
            return self.repository.get_employee_by_id(int(identifier))
        return self.repository.get_employee_by_code(identifier)

    def create_employee(self, emp_in: EmployeeCreate) -> Dict[str, Any]:
        """
        Registers a new employee. Validates uniqueness of employee_code and email.
        """
        # Check code uniqueness
        existing_code = self.repository.get_employee_by_code(emp_in.employee_code)
        if existing_code:
            raise ValueError(f"Employee code '{emp_in.employee_code}' already exists.")

        # Check email uniqueness
        existing_email = self.repository.get_employee_by_email(emp_in.email)
        if existing_email:
            raise ValueError(f"Email '{emp_in.email}' is already registered to another employee.")

        created = self.repository.create_employee(emp_in)
        app_logger.info(f"Registered new employee: {created['employee_code']} ({created['first_name']} {created['last_name']})")
        return created

    def update_employee(self, employee_id: int, update_in: EmployeeUpdate) -> Optional[Dict[str, Any]]:
        """Updates employee information."""
        existing = self.repository.get_employee_by_id(employee_id)
        if not existing:
            return None

        if update_in.email and update_in.email != existing["email"]:
            email_owner = self.repository.get_employee_by_email(update_in.email)
            if email_owner and email_owner["id"] != employee_id:
                raise ValueError(f"Email '{update_in.email}' is already in use by employee {email_owner['employee_code']}.")

        return self.repository.update_employee(employee_id, update_in)

    def deactivate_employee(self, employee_id: int) -> bool:
        """Deactivates an employee."""
        return self.repository.deactivate_employee(employee_id)
