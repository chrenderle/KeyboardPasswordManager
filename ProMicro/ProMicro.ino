#include <Wire.h>
#include <ArduinoQueue.h>

// queue for storing the key events
ArduinoQueue <uint8_t> queue(20);

// the pins for the columns
#define col_n 7
#define col0 A2
#define col1 A1
#define col2 A0
#define col3 15
#define col4 14
#define col5 16
#define col6 10
uint8_t col[col_n] = {col0, col1, col2, col3, col4, col5, col6};

// the pins for the rows
#define row_n 5
#define row0 4
#define row1 6
#define row2 7
#define row3 8
#define row4 9
uint8_t row[row_n] = {row0, row1, row2, row3, row4};

// contains the states of the previous polling round
uint8_t previous_keys[col_n * row_n];
// contains the states of the current polling round
uint8_t keys[col_n * row_n];

void send(uint8_t, uint8_t);
void requestEvent();

enum event {
    key_press,
    key_release
};

void setup() {
    // set all column pins to input and active the pull up resistor
    for (unsigned int i = 0; i < col_n; i++) {
        pinMode(col[i], INPUT);
        pinMode(col[i], INPUT_PULLUP);
    }

    // set all row pins to output and set the value to high
    for (unsigned int i = 0; i < row_n; i++) {
        pinMode(row[i], OUTPUT);
        digitalWrite(row[i], HIGH);
    }

    // initialize keys array with 0
    for (unsigned int i = 0; i < col_n * row_n; i++) {
        keys[i] = 0;
    }

    // initialize previous_keys array with 0
    for (unsigned int i = 0; i < col_n * row_n; i++) {
        previous_keys[i] = 0;
    }

    // begin i2c with slave address 8
    Wire.begin(8);
    // register event for requests
    Wire.onRequest(requestEvent);
}

void loop() {
    // loop through all row pins and set them low one by one
    for (uint8_t i = 0; i < row_n; i++) {
        digitalWrite(row[i], LOW);
        // loop through all column pins and if one is low it means that the corresponding button got pressed
        for (uint8_t i2 = 0; i2 < col_n; i2++) {
            keys[i * col_n + i2] = !digitalRead(col[i2]);
        }
        digitalWrite(row[i], HIGH);
    }

    // compare the previous keys with the current keys
    for (uint8_t i = 0; i < col_n * row_n; i++) {
        if (previous_keys[i] != keys[i]) {
            if (keys[i] == HIGH) {
                send(key_press, i);
            } else if (keys[i] == LOW) {
                send(key_release, i);
            }
        }
    }

    // copy the current keys to the previous keys
    memcpy(previous_keys, keys, sizeof(keys));

    // delay 10ms so we get a refresh rate of ~100Hz
    delay(10);
}

// gets called on an i2c request
void requestEvent() {
    // check if queue is empty
    if (!queue.isEmpty()) {
        // if queue is not empty send back the next item from the queue
        Wire.write(queue.dequeue());
    } else {
        // if queue is empty send back 1 which stands for no key press
        Wire.write(1);
    }
}

void send(uint8_t _event, uint8_t key) {
    // increase key by 2 because i2c cant handle 0 and 1 means no press
    key += 2;
    // if the event is a key release add 35 (col_n * row_n)
    if (_event == key_release) {
        key += col_n * row_n;
    }
    // enqueue the read key event
    queue.enqueue(key);
}

