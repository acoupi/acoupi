# Create Custom Components

To create a custom component that will play nicely with Acoupi it is best to
follow the following guidelines:

1. If the component you wish to implement can be categorized as one of the
   categories described above, then it should inherit from the corresponding
   base class and try to stick with the suggested interface. For example, if you are implementing a component that will be in charge of recording audio, then it should inherit from the `AudioRecorder` class.

2. If the component you wish to implement does not fit into any of the the
   mentioned categories, then it should try to have a simple interface that uses the data schema defined in `data_schema`. This will allow the component to be easily combined with other components defined in Acoupi.

3. If you wish to share your component with the Acoupi community, then make sure you checkout the `acoupi-contributing` section!