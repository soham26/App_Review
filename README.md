# Google Play Store Review Analyzer

A Python application with GUI for analyzing Google Play Store app reviews. Fetch app details, scrape reviews, analyze ratings distribution, and generate visualizations.

## Features

- 📱 **App Details Fetching**: Get comprehensive app information (title, rating, installs, etc.)
- 📊 **Review Analysis**: Scrape and analyze app reviews with detailed statistics
- 📈 **Visualizations**: Generate ratings distribution charts
- 💾 **Data Export**: Save results as CSV, JSON, and PNG files
- 🎨 **User-Friendly GUI**: Clean Tkinter interface with progress tracking

## Requirements

- Python 3.7+
- See `requirements.txt` for dependencies

## Installation

1. Clone this repository:
```bash
git clone https://github.com/soham26/App_Review.git
cd App_Review
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python reviewanalyser.py
```

1. Enter the app package name (e.g., `com.whatsapp`)
2. Click "Analyze App"
3. View results in the output area
4. Check the `results/{app_id}/` folder for saved files

## Output Files

Results are organized by app ID in the `results/` directory:
- `reviews_{timestamp}.csv` - All scraped reviews
- `app_details_{timestamp}.json` - App metadata
- `ratings_distribution_{timestamp}.png` - Ratings chart

## Example App Package Names

- WhatsApp: `com.whatsapp`
- Instagram: `com.instagram.android`
- Facebook: `com.facebook.katana`

## Technologies Used

- `google-play-scraper` - For fetching Play Store data
- `pandas` - Data manipulation and analysis
- `matplotlib` - Data visualization
- `tkinter` - GUI framework

## License

This project is open source and available under the MIT License.

## Contributing

Contributions, issues, and feature requests are welcome!

