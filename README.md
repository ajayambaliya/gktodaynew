# CurrentAdda - Modern Current Affairs PDF Generator

A modern, magazine-style PDF generator for current affairs with Gujarati translation and Telegram integration.

## Features

- **Modern Design**: Premium magazine-style layout with modern UI/UX principles
- **Bilingual**: Automatically translates content to Gujarati
- **PDF Generation**: Creates beautiful PDFs with WeasyPrint
- **Telegram Integration**: Automatically posts to the @CurrentAdda Telegram channel
- **Automation**: Runs daily via GitHub Actions
- **Responsive**: Looks great on all devices

## Setup

### Prerequisites

- Python 3.8 or higher
- Pip package manager
- For Windows users: GTK libraries for WeasyPrint (see below)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/gktodayapp.git
   cd gktodayapp
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. **Windows Users Only**: Install GTK for WeasyPrint
   - Download and install GTK3 from [here](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases)
   - Make sure to check "Add to PATH" during installation
   - Restart your terminal after installation

4. Set up environment variables:
   
   Create a `.env` file in the root directory with:
   ```
   TELEGRAM_BOT_TOKEN=6206446036:AAHtVn9LAvdRUtjCLmz1_49v5xRPSanTD1g
   ```

### Running Locally

Run the main script:
```
python main.py
```

The script will:
1. Fetch latest articles from GKToday
2. Translate content to Gujarati
3. Generate a modern PDF
4. Send the PDF to your Telegram channel

## GitHub Actions Setup

The project is configured to run automatically via GitHub Actions.

1. In your GitHub repository, go to Settings > Secrets and Variables > Actions
2. Add a new repository secret:
   - Name: `TELEGRAM_BOT_TOKEN`
   - Value: Your Telegram bot token

The workflow will run daily at 5:00 PM IST (11:30 UTC).

## Project Structure

- `main.py`: Main entry point that orchestrates the process
- `scraper.py`: Functions for fetching and processing content
- `translation.py`: Handles translation to Gujarati
- `pdf_generator.py`: Generates modern PDF files
- `telegram_sender.py`: Sends PDFs to Telegram
- `config.py`: Configuration settings
- `templates/`: HTML templates for PDF generation
- `output/`: Generated PDF files
- `.github/workflows/`: GitHub Actions workflow configuration

## Customization

- Modify `templates/pdf_template.html` to change PDF appearance
- Adjust article count in `config.py`
- Change Telegram channel details in `config.py`

## License

This project is open source and available under the MIT License.

## Contact

Join our Telegram channel: [Current Adda](https://t.me/CurrentAdda) 