# CSCalendar

This is *cscalendar*, a small python shell
utility to automagically generate an iCal file with your schedule!

The utility has been tailored to fit the rather *unusual* requirements of
UWC CSC, starting (and hopefully stopping) from the school year 2017/2018.

To run, clone the project and execute the script with

    python main.py "name surname" "DP"

If you’d like to use the GUI, then you need to install Gooey with

    pip install Gooey

and run the script with

    python gui.py

# Arguments 

The script has two positional arguments: Name and DP. The name is a string
containing your name, as it appears in the class declaration files (the
official spreadsheet released by the school). If your name is written in
more than one way, then input the preferred (most frequent) way and
manually override the missing blocks.

DP is your DP class. It is used to automagically parse the schedule file.
It can be one of the following: DP1, DP2, or preDP. 

The block override options are -a, -b, ..., -f. By using these options,
you override (or manually add) your classes. 
