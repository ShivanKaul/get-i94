# Get I-94

The `run.py` script fetches your latest I-94 from the CBP website and saves it as a PDF locally. The script uses Selenium and the Brave browser (though you can easily change it to be Chrome). You can save your I-94 details locally in a file called `i94_config.json` (DO NOT UPLOAD THIS ANYWHERE). I've included `i94_config.json.sample` as a kick-off point but you'll need to obviously change and rename the file.

## Installation

```bash
# Virtualenv
python3 venv venv
source venv/bin/activate
# Install dependencies
pip install -r requirements.txt
```

The script needs a path to a browser binary. I've hardcoded a path to a local installation of Brave, but you can easily change this.
The script also needs [ChromeDriver](https://developer.chrome.com/docs/chromedriver/downloads). I installed it using `brew`:

```bash
brew install chromedriver
```
Again, you can change the path to your local install of ChromeDriver in the `run.py` script.

## Run

```bash
python3 run.py
```

## Debugging

If you get error messages, try running the script in non-headless (regular mode) first and adding `wait`s.
