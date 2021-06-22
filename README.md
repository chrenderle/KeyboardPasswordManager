# Keyboard Password-Manager
## What is this?
This is a keyboard with an integrated password manager based on the [Redox Keyboard](https://github.com/mattdibi/redox-keyboard).
The keyboard works like a normal keyboard with a custom German layout. It is possible to configure the layout to any layout you want.
## BOM (Bill of Materials)
* Raspberry Pi Zero (W is useful for developing but not necessary)
* All the materials for a normal [Redox Keyboard](https://github.com/mattdibi/redox-keyboard) except only one Arduino Pro Micro is needed
* One 3v3 to 5v level converter like [this](https://www.amazon.de/ARCELI-Converter-Bidirektionales-Shifter-Arduino/dp/B07RDHR315/ref=sr_1_2?__mk_de_DE=%C3%85M%C3%85%C5%BD%C3%95%C3%91&dchild=1&keywords=3v3+5v+converter&qid=1618253286&sr=8-2) one
* currently, around 30 jumper cables (female to female)
## Code Structure
The code is structured in two parts. The first part is the code for the Arduino Pro Micro and is located in the folder "ProMicro".
The other part is for the Raspberry Pi Zero, contains the main part of the project and is located in the folder "RaspberryPiZero".
The file "Main.py" contains the code which is executed on boot of the RaspberryPi. It uses two packages "GUI" and "Keyboard" which contain the classes for the GUI and the keyboard.
## Todo
This section contains the todos I still need to add to the readme. If you want me too give this some priority write me an email to mail@chrenderle.de, otherwise this can be ignored.
* Installation
* Creating a custom layout
* Using the password manager
* some pictures (when there is a nice looking prototype)