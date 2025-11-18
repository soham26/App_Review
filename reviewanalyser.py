from google_play_scraper import app, reviews_all, Sort
import pandas as pd
# Set matplotlib backend BEFORE importing pyplot to avoid GUI conflicts on macOS
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from collections import Counter
from datetime import datetime
import json
import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from threading import Thread
import queue

class PlayStoreAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Google Play Store Review Analyzer")
        self.root.geometry("800x600")
        self.analyzer = PlayStoreAnalyzer()
        self.analyzer.root = root  # Give analyzer access to root for threading
        
        # Queue for thread-safe communication
        self.message_queue = queue.Queue()
        
        # Setup button styles
        self.setup_button_styles()
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # App ID input
        ttk.Label(self.main_frame, text="Enter App Package Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.app_id_var = tk.StringVar(value="com.whatsapp")
        self.app_id_entry = ttk.Entry(self.main_frame, textvariable=self.app_id_var, width=40)
        self.app_id_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Analyze button with custom style
        self.analyze_button = ttk.Button(
            self.main_frame, 
            text="Analyze App", 
            command=self.start_analysis,
            style='CTA.TButton'
        )
        self.analyze_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Output text area
        self.output_area = scrolledtext.ScrolledText(self.main_frame, width=80, height=30)
        self.output_area.grid(row=1, column=0, columnspan=3, pady=10)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(self.main_frame, variable=self.progress_var, maximum=100)
        self.progress.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(self.main_frame, textvariable=self.status_var)
        self.status_label.grid(row=3, column=0, columnspan=3)
        
        # Redirect stdout to the text widget (thread-safe)
        self.redirect_stdout()
        
        # Check for messages from background thread
        self.root.after(100, self.process_queue)
    
    def setup_button_styles(self):
        """Configure CTA button styles for active and disabled states"""
        style = ttk.Style()
        
        # CTA Button Colors
        # Active state: Modern blue (#007AFF - iOS blue, professional and trustworthy)
        # Disabled state: Light gray (#CCCCCC - clearly indicates inactive state)
        
        # Active state styling
        style.configure(
            'CTA.TButton',
            background='#007AFF',  # Modern blue
            foreground='white',     # White text for contrast
            borderwidth=0,
            focuscolor='none',
            padding=(20, 10)        # Comfortable padding
        )
        
        # Hover/pressed/disabled states (using map for state-based styling)
        style.map(
            'CTA.TButton',
            background=[
                ('active', '#0056CC'),      # Hover state - darker blue
                ('pressed', '#004499'),     # Pressed state - darkest blue
                ('disabled', '#CCCCCC')     # Disabled state - light gray
            ],
            foreground=[
                ('active', 'white'),        # Hover text - white
                ('pressed', 'white'),       # Pressed text - white
                ('disabled', '#666666')     # Disabled text - darker gray
            ]
        )
    
    def redirect_stdout(self):
        """Thread-safe stdout redirection"""
        class TextRedirector:
            def __init__(self, widget, queue):
                self.widget = widget
                self.queue = queue

            def write(self, text):
                # Put message in queue for main thread to process
                self.queue.put(('text', text))

            def flush(self):
                pass

        import sys
        sys.stdout = TextRedirector(self.output_area, self.message_queue)
    
    def process_queue(self):
        """Process messages from background thread"""
        try:
            while True:
                msg_type, data = self.message_queue.get_nowait()
                if msg_type == 'text':
                    self.output_area.insert(tk.END, data)
                    self.output_area.see(tk.END)
                elif msg_type == 'progress':
                    self.progress_var.set(data)
                elif msg_type == 'status':
                    self.status_var.set(data)
                elif msg_type == 'error':
                    messagebox.showerror("Error", data)
                    self.analyze_button.state(['!disabled'])
                elif msg_type == 'success':
                    messagebox.showinfo("Success", data)
                    self.status_var.set("Analysis complete!")
                    self.progress_var.set(100)
                    self.analyze_button.state(['!disabled'])
                elif msg_type == 'enable_button':
                    self.analyze_button.state(['!disabled'])
        except queue.Empty:
            pass
        finally:
            # Schedule next check
            self.root.after(100, self.process_queue)
    
    def start_analysis(self):
        # Clear previous output
        self.output_area.delete('1.0', tk.END)
        self.analyze_button.state(['disabled'])
        self.status_var.set("Analyzing...")
        self.progress_var.set(0)
        
        # Get app_id in MAIN thread before starting background thread
        # This prevents autorelease pool crashes on macOS
        app_id = self.app_id_var.get().strip()
        
        # Pass queue to analyzer for thread-safe updates
        self.analyzer.message_queue = self.message_queue
        
        # Run analysis in a separate thread, passing app_id as argument
        Thread(target=self.run_analysis, args=(app_id,), daemon=True).start()
    
    def run_analysis(self, app_id):
        """Run analysis in background thread - all GUI updates via queue"""
        try:
            if not app_id:
                self.message_queue.put(('error', "Please enter an app package name"))
                self.message_queue.put(('status', "Ready"))
                self.message_queue.put(('progress', 0))
                return
            
            self.message_queue.put(('progress', 20))
            self.analyzer.analyze_app(app_id)
            self.message_queue.put(('progress', 100))
            self.message_queue.put(('success', "Analysis completed successfully!"))
        except Exception as e:
            self.message_queue.put(('status', "Error occurred!"))
            self.message_queue.put(('error', str(e)))
            self.message_queue.put(('progress', 0))
        finally:
            # Re-enable button via queue (always runs, even on early return)
            self.message_queue.put(('enable_button', None))

class PlayStoreAnalyzer:
    def __init__(self):
        self.app_details = None
        self.reviews_df = None
        self.root = None  # Will be set by GUI
        self.ratings_dist = None
        self.message_queue = None  # Will be set by GUI for thread-safe updates
        self.current_app_id = None  # Store current app_id for file organization
        
    def analyze_app(self, app_id):
        """
        Analyze a single app by its package name (app_id)
        """
        self.current_app_id = app_id  # Store app_id for file organization
        print(f"\nAnalyzing app: {app_id}")
        
        # Get app details
        try:
            self.app_details = app(app_id)
            print("\nApp Details:")
            print(f"Title: {self.app_details['title']}")
            print(f"Current Rating: {self.app_details['score']}")
            print(f"Total Reviews: {self.app_details['reviews']}")
            print(f"Installs: {self.app_details['installs']}")
            print(f"Updated: {self.app_details['updated']}")
        except Exception as e:
            print(f"Error fetching app details: {e}")
            return
        
        # Get all reviews
        try:
            result = reviews_all(
                app_id,
                lang='en',
                country='us',
                sort=Sort.MOST_RELEVANT
            )
            self.reviews_df = pd.DataFrame(result)
            
            # Basic analysis
            self.analyze_ratings()
            self.analyze_reviews()
            
            # Save data
            self.save_results(app_id)
            
        except Exception as e:
            print(f"Error fetching reviews: {e}")
    
    def analyze_ratings(self):
        """Analyze ratings distribution"""
        if self.reviews_df is None:
            return
        
        print("\nRatings Distribution:")
        self.ratings_dist = self.reviews_df['score'].value_counts().sort_index()
        for rating, count in self.ratings_dist.items():
            print(f"{rating} stars: {count} reviews ({count/len(self.reviews_df)*100:.1f}%)")
        
        # Create plot directly (Agg backend is thread-safe)
        self.create_plot()
    
    def analyze_reviews(self):
        """Analyze review content"""
        if self.reviews_df is None:
            return
        
        print("\nReview Analysis:")
        print(f"Total Reviews Analyzed: {len(self.reviews_df)}")
        
        # Average review length
        self.reviews_df['review_length'] = self.reviews_df['content'].str.len()
        avg_length = self.reviews_df['review_length'].mean()
        print(f"Average Review Length: {avg_length:.1f} characters")
        
        # Most recent reviews
        print("\nMost Recent Reviews:")
        recent_reviews = self.reviews_df.sort_values('at', ascending=False).head(5)
        for _, review in recent_reviews.iterrows():
            print(f"\nRating: {review['score']} stars")
            print(f"Date: {review['at']}")
            print(f"Content: {review['content'][:200]}...")
    
    def save_results(self, app_id):
        """Save analysis results to files organized by app"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create directory structure: results/{app_id}/
        results_dir = os.path.join("results", app_id)
        os.makedirs(results_dir, exist_ok=True)
        
        # Save reviews to CSV
        if self.reviews_df is not None:
            csv_path = os.path.join(results_dir, f"reviews_{timestamp}.csv")
            self.reviews_df.to_csv(csv_path, index=False)
            print(f"\nReviews saved to {csv_path}")
        
        # Save app details to JSON
        if self.app_details is not None:
            json_path = os.path.join(results_dir, f"app_details_{timestamp}.json")
            with open(json_path, 'w') as f:
                json.dump(self.app_details, f, indent=4)
            print(f"App details saved to {json_path}")
    
    def create_plot(self):
        """Create the ratings distribution plot and save in app-specific directory"""
        if self.current_app_id is None:
            print("Warning: Cannot save plot - app_id not set")
            return
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create directory structure: results/{app_id}/
        results_dir = os.path.join("results", self.current_app_id)
        os.makedirs(results_dir, exist_ok=True)
        
        # Create and save plot
        plt.figure(figsize=(10, 6))
        self.ratings_dist.plot(kind='bar')
        plt.title('Ratings Distribution')
        plt.xlabel('Rating')
        plt.ylabel('Number of Reviews')
        plt.tight_layout()
        
        plot_path = os.path.join(results_dir, f"ratings_distribution_{timestamp}.png")
        plt.savefig(plot_path)
        plt.close()
        print(f"Ratings plot saved to {plot_path}")

def main():
    root = tk.Tk()
    app = PlayStoreAnalyzerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()