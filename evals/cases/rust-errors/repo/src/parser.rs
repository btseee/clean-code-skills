pub struct Config {
    pub port: u16,
    pub timeout_secs: u64,
}

pub fn parse_config(input: &str) -> Config {
    let mut port = 0u16;
    let mut timeout_secs = 0u64;
    for line in input.lines() {
        let (key, value) = line.split_once('=').unwrap();
        match key.trim() {
            "port" => port = value.trim().parse().unwrap(),
            "timeout_secs" => timeout_secs = value.trim().parse().unwrap(),
            _ => {}
        }
    }
    Config { port, timeout_secs }
}
