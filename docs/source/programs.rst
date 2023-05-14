Built-in Programs
=================

**Acoupi** comes with a set of built-in programs to get you started without any
additional configuration. These programs are designed to cover a range of use
cases in bioacoustics and environmental monitoring.

Simple
------

The ``simple`` program is the basic use case of **Acoupi**. If you just want to
record audio from the microphone and save it to a file, this program is for
you. It's easy to configure when to start and stop recording, the interval
between each recording, and the duration of each recording. With these
settings, you can make **Acoupi** behave like an AudioMoth.

BatDetect2
----------

The ``batdetect2`` program is a bat detector that not only records audio from
the microphone but also performs real-time bat detection and classification
using the BatDetect2 model. With ``batdetect2``, you can store the detections
and even send them to a remote server for further processing. It's great for
researchers or environmental consultants who want to identify bat species in
real-time.

BirdNET
-------

The ``birdnet`` program is similar to the bat detector, but it's for bird
detection and classification. It uses the BirdNET model to detect and classify
bird sounds in real-time. If you're interested in monitoring bird populations
or studying bird behavior, this program is perfect for you.

To use any of these programs, simply select it during setup by typing acoupi
setup and then follow the prompts to configure the program. You can always
modify the configuration later by typing acoupi config edit.

----

That's it! With **Acoupi**'s built-in programs, you'll be up and running in no
time. If you want to create your own custom program, check out the instructions
in the :ref:`next section<advanced-guide>`.
