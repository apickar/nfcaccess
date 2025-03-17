use pn532::{Pn532, interface::i2c::I2CInterface};
use rppal::gpio::Gpio;
use std::{thread, time::Duration};

// Define GPIO pins for the relay, LED, and buzzer
const RELAY_PIN: u8 = 17;  // GPIO17 for the relay
const LED_PIN: u8 = 27;    // GPIO27 for the red LED
const BUZZER_PIN: u8 = 22; // GPIO22 for the buzzer

// Define authorized UIDs (example: "04aabbccdd")
fn is_authorized(uid: &str) -> bool {
    let authorized_uids = vec![
        "04aabbccdd", // Replace with actual UID values
        "1234567890",  // Replace with actual UID values
    ];
    authorized_uids.contains(&uid)
}

fn main() {
    // Initialize the GPIO for relay, LED, and buzzer control
    let gpio = Gpio::new().expect("Failed to access GPIO");
    let mut relay = gpio.get(RELAY_PIN).expect("Failed to get GPIO pin for relay").into_output();
    let mut led = gpio.get(LED_PIN).expect("Failed to get GPIO pin for LED").into_output();
    let mut buzzer = gpio.get(BUZZER_PIN).expect("Failed to get GPIO pin for buzzer").into_output();

    // Initialize the NFC reader (I2C)
    let i2c = I2CInterface::new("/dev/i2c-1").expect("Failed to initialize I2C interface");
    let mut pn532 = Pn532::new(i2c);
    
    pn532.init().expect("Failed to initialize PN532");

    loop {
        // Poll for NFC card
        if let Some(uid) = pn532.read_passive_target() {
            println!("UID: {}", uid);
            if is_authorized(&uid) {
                println!("Access granted");
                
                // Unlock the door (activate relay) for 5 seconds
                relay.set_high(); // Unlock the door
                thread::sleep(Duration::from_secs(5));
                relay.set_low(); // Lock the door again

                // Turn off the LED and buzzer if previously activated
                led.set_low();
                buzzer.set_low();
            } else {
                println!("Access denied");

                // Light the red LED and sound the buzzer
                led.set_high();  // Turn on the red LED
                buzzer.set_high(); // Sound the buzzer
                thread::sleep(Duration::from_secs(1)); // Keep the LED and buzzer on for 1 second
                led.set_low();  // Turn off the red LED
                buzzer.set_low(); // Turn off the buzzer
            }
        } else {
            println!("No card detected");
            // Ensure all outputs are turned off when no card is detected
            relay.set_low();
            led.set_low();
            buzzer.set_low();
        }

        // Wait a moment before checking again
        thread::sleep(Duration::from_millis(500));
    }
}