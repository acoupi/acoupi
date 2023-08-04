"""Test Acoupi Program."""
from acoupi.programs.configs import BaseConfigSchema
from acoupi.programs.base import AcoupiProgram


class TestConfigSchema(BaseConfigSchema):
    """Configuration Schema for Test Program."""

    name: str = "test_program"

    @classmethod
    def add_arguments(cls, parser):
        """Add arguments to the parser."""
        parser.add_argument(
            "--name",
            type=str,
            default="test_program",
            help="Name of the test program",
        )


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
