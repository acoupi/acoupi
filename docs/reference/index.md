# Acoupi Technical Reference

The _acoupi Reference Section_ is helpful to find technical informations about the inner-workings of acoupi and how it operates. In the following section, 
you will find more about the available acoupi functions. 

- [Data](data): Responsible for defining a standardised data structure and ensuring that the flow of information 
    between the other layers is validated and consistent. The data schema is composed of multiple data objects built
    using the Pydantic library, these correspond to attributes of Python classes.

- [Compoments](components): Form the building blocks of acoupi. They are individual elements (i.e., Python classes) designed
    to perform specific actions based on the configurations of a user. Their inputs and outputs follow the structure
    of the data.

- [Task](tasks): Integrate a sequence of one or more components executed in a specific flow. 

- [Programs](programs): Illustrate the complete set of tasks, components, and data schema. 

- [System](system): Detailed functions used to manage running acoupi application. 


<table>
    <tr>
        <td>
            <a href="data">Data</a>
                <td>
                    <p>Ensure data validation and consistency.</p>
                </td>
        </td>
    </tr>
    <tr>
        <td>
            <a href="components">Components</a>
                <td>
                    <p>Building blocks of acoupi.</p>
                </td>
        </td>
    </tr>
    <tr>
        <td>
            <a href="tasks">Tasks</a>
                <td>
                    <p>Integrate sequences of one or more compoments.</p>
                </td>
        </td>
    </tr>
    <tr>
        <td>
            <a href="programs">Programs</a>
                <td>
                <p>Complete unit running on acoupi.</p>
                </td>
        </td>
    </tr>
    <tr>
        <td>
            <a href="system">System</a>
                <td>
                    <p>System Function.</p>
                </td>
        </td>
    </tr>
</table>