# Installation

To install and use the bare-bone framework of acoupi on your embedded device follow these steps: 

**Step 1:** Install acoupi and its dependencies
```bash
pip install acoupi
```
**Step 2:** Configure acoupi default program. (*acoupi comes with a test and a default program. The default program is only recording and saving audio files based on the users' settings. Think like something similar to the setup of an AudioMoth*). 
```bash
acoupi setup --program `program-name`
```
For acoupi default program, enter this command: 
```bash
acoupi setup --program acoupi.programs.custom.acoupi
```
**Step 3:** To start acoupi run the command: 
```bash
acoupi start
```

Sometimes the programs might have some additional or different installation requirements. We recommend reading the documentation of the program you want to install.
