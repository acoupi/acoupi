"""Test Acoupi Program."""
from acoupi.programs.base import AcoupiProgram
from pydantic import BaseModel


class TestConfigSchema(BaseModel):
    """Configuration Schema for Test Program."""

    name: str = "test_program"


class TestProgram(AcoupiProgram):
    """Test Program."""

    config: TestConfigSchema

    def setup(self, config: TestConfigSchema):
        """Setup Test Program."""
        print("Setting up test program")

        def test_task():
            """Simple task."""
            print(f"Configuration: name={config.name}")
            print("Task executed")

        # Schedule the task to run every 10 seconds
        self.add_task(test_task, schedule=10)
