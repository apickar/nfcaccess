use pn532::interface::i2c::I2CInterface;
use pn532::Pn532;
use rppal::gpio::Gpio;
use std::thread;
use std::time::Duration;

const RELAY_PIN: u8 = 17; // GPIO17 for the relay

// Define authorized UIDs (example: "04aabbccdd")
fn is_authorized(uid: &str) -> bool {
    let authorized_uids = vec![
        "04aabbccdd", // Replace with actual UID values
        "1234567890"
    ];
    authorized_uids.contains(&uid)
}

fn main() {
    // Initialize the GPIO for relay control
    let gpio = Gpio::new().expect("Failed to access GPIO");
    let mut relay = gpio.get(RELAY_PIN).expect("Failed to get GPIO pin").into_output();
    
    // Initialize NFC reader (I2C)
    let i2c = I2CInterface::new("/dev/i2c-1").expect("Failed to open I2C");
    let mut nfc = Pn532::new(i2c);
    
    // Wake up NFC module
    nfc.wake_up().expect("Failed to wake up PN532");

    println!("Waiting for NFC card...");

    loop {
        // Try reading an NFC card
        match nfc.read_passive_target_id() {
            Ok(Some(uid)) => {
                let uid_str = hex::encode(uid);  // Convert UID to hex string
                println!("Card detected! UID: {}", uid_str);

                // Check if the card UID is in the authorized list
                if is_authorized(&uid_str) {
                    println!("Access granted! Unlocking door...");
                    relay.set_high(); // Activate relay
                    thread::sleep(Duration::from_secs(5)); // Keep unlocked for 5 seconds
                    relay.set_low(); // Lock again
                    println!("Locking door...");
                } else {
                    println!("Access denied!");
                    // Add code for access denied

                }
            }
            _ => {} // No card detected
        }

        thread::sleep(Duration::from_millis(500)); // Avoid constant polling
    }
}