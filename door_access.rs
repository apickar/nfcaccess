use pn532::interface::i2c::I2CInterface;
use pn532::Pn532;
use rppal::gpio::{Gpio, OutputPin};
use std::{thread, time};

const RELAY_PIN: u8 = 17; // GPIO17 for relay control
const LED_RED_PIN: u8 = 27; // GPIO27 for red LED (access denied)
const BUZZER_PIN: u8 = 22; // GPIO22 for buzzer (access denied)

// Define authorized UIDs
fn is_authorized(uid: &str) -> bool {
    let authorized_uids = vec![
        "04aabbccdd", // Replace with actual UID values
        "1234567890",
    ];
    authorized_uids.contains(&uid)
}

fn main() {
    // Initialize GPIO
    let gpio = Gpio::new().expect("Failed to access GPIO");
    let mut relay = gpio.get(RELAY_PIN).expect("Failed to get relay pin").into_output();
    let mut led_red = gpio.get(LED_RED_PIN).expect("Failed to get red LED pin").into_output();
    let mut buzzer = gpio.get(BUZZER_PIN).expect("Failed to get buzzer pin").into_output();

    // Initialize NFC reader (I2C)
    let i2c = I2CInterface::new("/dev/i2c-1").expect("Failed to initialize I2C");
    let mut nfc = Pn532::new(i2c);

    println!("Waiting for NFC card...");
    loop {
        if let Ok(Some(uid)) = nfc.read_passive_target() {
            let uid_str = uid.iter().map(|b| format!("{:02x}", b)).collect::<String>();
            println!("Card UID: {}", uid_str);
            
            if is_authorized(&uid_str) {
                println!("Access Granted");
                relay.set_high();
                thread::sleep(time::Duration::from_secs(3)); // Keep relay open for 3 sec
                relay.set_low();
            } else {
                println!("Access Denied");
                led_red.set_high();
                buzzer.set_high();
                thread::sleep(time::Duration::from_secs(2)); // Buzzer and LED stay on for 2 sec
                led_red.set_low();
                buzzer.set_low();
            }
        }
        thread::sleep(time::Duration::from_millis(500)); // Poll every 500ms
    }
}