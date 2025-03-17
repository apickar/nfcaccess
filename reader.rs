use pn532::interface::i2c::I2CInterface;
use pn532::Pn532;
use std::thread;
use std::time::Duration;

fn main() {
    // Initialize NFC reader (I2C)
    let i2c = I2CInterface::new("/dev/i2c-1").expect("Failed to open I2C");
    let mut nfc = Pn532::new(i2c);
    
    // Wake up NFC module
    nfc.wake_up().expect("Failed to wake up PN532");

    println!("Waiting for NFC card...");

    loop {
        match nfc.read_passive_target_id() {
            Ok(Some(uid)) => {
                let uid_str = hex::encode(uid);  // Convert UID to hex
                println!("Card detected! UID: {}", uid_str);
            }
            _ => {} // No card detected
        }
        
        thread::sleep(Duration::from_millis(500)); // Avoid constant polling
    }
}