# Creating a new data object

Creating a new data object with Pydantic involves defining a Python class that inherits from `pydantic.BaseModel`.
This class acts as a blueprint for instances of the data object, specifying the attributes and their types.
The keys steps and requirements for creating a new _acoupi_ data objects are the following:

Step 1: In `/src/acoupi/data.py` define a data object class that inherit from `BaseModel`.

!!! Example "New Data Object." 

    ```python
    from pydantic import BaseModel

    class YourDataObject(BaseModel):
        # Attributes for the class
    ```

Step 2: Declare the attributes of the new data object as the class variables.
      Specify the attributes' data types using Python type hints.
      Optionally, set default values for the attributes.

!!! Example "Adding Attributes."

    ```python
    from pydantic import BaseModel
    from pathlib import Path

    class YourDataObject(BaseModel):
        attribute1: float = 0.5
        """Attribute 1"""

        attribute2: str
        """Attribute 2"""

        attribute3: Path
        """Attribute 3"""
    ```

Step 3 *(Optional)*: Implement custom validation logic using [**Pydantic's validation methods**](https://docs.pydantic.dev/dev/concepts/validators/#annotated-validators) such as `@field_validatior` and `@model_validator`.

!!! Example "Add custom validation logic"

    ```python 
    from pydantic import BaseModel, field_validator

    class YourDataObject(BaseModel):
        attribute1: int = 0.5
        attribute2: str

        @field_validator("attribute1")
        def validate_attribute1(cls, value):
        """Check that attribute1 is a float between 0 and 1."""
        if value < 0 or value > 1:
                raise ValueError("attribute1 must be between 0 and 1")
            return value
    ```
