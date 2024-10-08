"""Test Acoupi Program."""

from pydantic import BaseModel

from acoupi.programs.core.base import AcoupiProgram
from acoupi.system.exceptions import HealthCheckError


class TestConfigSchema(BaseModel):
    """Configuration Schema for Test Program."""

    name: str = "test_program"


class TestProgram(AcoupiProgram[TestConfigSchema]):
    """Test Program."""

    config_schema = TestConfigSchema

    def setup(self, config: TestConfigSchema):
        """Set up Test Program."""

        def test_task():
            """Simple task."""
            print(f"Configuration: name={config.name}")
            print("Task executed")

        # Schedule the task to run every 10 seconds
        self.add_task(test_task, schedule=10)

    def check(self, config: TestConfigSchema):
        """Check the configurations."""
        print("Checking test program configurations")
        if config.name != "test_program":
            raise HealthCheckError("name is not test_program")
