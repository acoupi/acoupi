# Acoupi Technical Reference

The _acoupi Reference Section_ is helpful to find technical information about the inner-workings of _acoupi_ and how it operates.
In the following section, you will find more about the available _acoupi_ functions.

- [Data](data.md): Responsible for defining a standardised data structure and ensuring that the flow of information between the other layers is validated and consistent.
    The data schema is composed of multiple data objects built using the Pydantic library, these correspond to attributes of Python classes.

- [Components](components.md): Form the building blocks of acoupi.
    They are individual elements (i.e., Python classes) designed to perform specific actions based on the configurations of a user.
    Their inputs and outputs follow the structure of the data.

- [Task](tasks.md): Integrate a sequence of one or more components executed in a specific flow.

- [Programs](programs.md): Illustrate the complete set of tasks, components, and data schema.

- [System](system.md): Detailed functions used to manage running acoupi application.

<table>
  <tr>
    <td>
      <a href="data">Data</a>
    </td>
    <td>
      <p>Ensure data validation and consistency.</p>
    </td>
  </tr>
  <tr>
    <td>
      <a href="components">Components</a>
    </td>
    <td>
      <p>Building blocks of acoupi.</p>
    </td>
  </tr>
  <tr>
    <td>
      <a href="tasks">Tasks</a>
    </td>
    <td>
      <p>Integrate sequences of one or more compoments.</p>
    </td>
  </tr>
  <tr>
    <td>
      <a href="programs">Programs</a>
    </td>
    <td>
      <p>Complete unit running on acoupi.</p>
    </td>
  </tr>
  <tr>
    <td>
      <a href="system">System</a>
    </td>
    <td>
      <p>System Function.</p>
    </td>
  </tr>
</table>
