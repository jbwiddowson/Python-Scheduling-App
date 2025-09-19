# scheduler_app.py

def main():
    """
    Main function that runs the command-line interface
    This handles all user interaction and coordinates the app's functionality
    """
    # Create the main application instance
    app = SchedulingApp()
    
    # Welcome message and show available commands
    print("=== Personal Scheduling App ===")
    print("Commands: add, remove, today, date, upcoming, quit")
    
    # Main command loop - keeps running until user types 'quit'
    while True:
        try:
            # Get command from user
            command = input("\nEnter command: ").lower().strip()
            
            # ========== QUIT COMMAND ==========
            if command == 'quit' or command == 'q':
                print("Goodbye!")
                break
            
            # ========== ADD APPOINTMENT COMMAND ==========
            elif command == 'add':
                print("\n--- Add New Appointment ---")
                
                # Get appointment details from user
                title = input("Title: ").strip()
                if not title:  # Title is required
                    print("Title cannot be empty")
                    continue
                
                # Get date and time information
                date_str = input("Date (YYYY-MM-DD): ").strip()
                start_time_str = input("Start time (HH:MM): ").strip()
                end_time_str = input("End time (HH:MM): ").strip()
                
                try:
                    # Convert strings to datetime objects
                    start_time = parse_datetime(date_str, start_time_str)
                    end_time = parse_datetime(date_str, end_time_str)
                except ValueError as e:
                    print(f"Error: {e}")
                    continue  # Go back to command prompt
                
                # Get optional details
                description = input("Description (optional): ").strip()
                location = input("Location (optional): ").strip()
                
                # Try to add the appointment
                app.add_appointment(title, start_time, end_time, description, location)
            
            # ========== REMOVE APPOINTMENT COMMAND ==========
            elif command == 'remove':
                print("\n--- Remove Appointment ---")
                # Show appointments so user can see IDs
                app.display_upcoming(30)  # Show more appointments for removal
                apt_id = input("\nEnter appointment ID (first 8 characters): ").strip()
                
                # Find the full ID from the partial ID user entered
                full_id = None
                for apt in app.appointments:
                    if apt.id.startswith(apt_id):  # Match partial ID
                        full_id = apt.id
                        break
                
                if full_id:
                    app.remove_appointment(full_id)
                else:
                    print("Appointment not found")
            
            # ========== SHOW TODAY'S SCHEDULE COMMAND ==========
            elif command == 'today':
                app.display_schedule()  # No date = today
            
            # ========== SHOW SPECIFIC DATE COMMAND ==========
            elif command == 'date':
                date_str = input("Enter date (YYYY-MM-DD): ").strip()
                try:
                    # Parse the date and show schedule for that day
                    date = datetime.strptime(date_str, '%Y-%m-%d')
                    app.display_schedule(date)
                except ValueError:# Import necessary libraries for the scheduling application
import json                          # For saving/loading appointment data to/from files
import os                           # For checking if files exist
from datetime import datetime, timedelta  # For handling dates and times
from typing import List, Dict, Optional   # For type hints to make code more readable

# ==================== APPOINTMENT CLASS ====================
# This class represents a single appointment/event in the schedule
class Appointment:
    def __init__(self, title: str, start_time: datetime, end_time: datetime, 
                 description: str = "", location: str = ""):
        """
        Initialize a new appointment with all necessary details
        Args:
            title: Name/title of the appointment
            start_time: When the appointment begins
            end_time: When the appointment ends  
            description: Optional details about the appointment
            location: Optional location where appointment takes place
        """
        self.id = self._generate_id()           # Create unique ID for this appointment
        self.title = title                      # Store appointment title
        self.start_time = start_time           # Store start date/time
        self.end_time = end_time               # Store end date/time
        self.description = description         # Store optional description
        self.location = location               # Store optional location
        
    def _generate_id(self) -> str:
        """
        Generate a unique ID based on current timestamp
        This creates a unique identifier for each appointment by using
        the current time in microseconds, ensuring no duplicates
        """
        return str(int(datetime.now().timestamp() * 1000000))
    
    def to_dict(self) -> Dict:
        """
        Convert appointment to dictionary format for JSON storage
        This allows us to save appointments to a file by converting
        all the appointment data into a format that can be stored
        """
        return {
            'id': self.id,
            'title': self.title,
            'start_time': self.start_time.isoformat(),  # Convert datetime to string
            'end_time': self.end_time.isoformat(),      # Convert datetime to string
            'description': self.description,
            'location': self.location
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        """
        Create appointment object from dictionary data (opposite of to_dict)
        This is used when loading appointments from a saved file
        Args:
            data: Dictionary containing appointment information
        Returns:
            Appointment object created from the dictionary data
        """
        # Create a new appointment with the loaded data
        appointment = cls(
            title=data['title'],
            start_time=datetime.fromisoformat(data['start_time']),  # Convert string back to datetime
            end_time=datetime.fromisoformat(data['end_time']),      # Convert string back to datetime
            description=data.get('description', ''),                # Use empty string if not found
            location=data.get('location', '')                       # Use empty string if not found
        )
        appointment.id = data['id']  # Restore the original ID
        return appointment
    
    def overlaps_with(self, other) -> bool:
        """
        Check if this appointment overlaps with another appointment
        This is crucial for detecting scheduling conflicts
        
        Logic: Two appointments overlap if:
        - This appointment starts before the other ends AND
        - This appointment ends after the other starts
        
        Args:
            other: Another Appointment object to check against
        Returns:
            True if appointments overlap, False otherwise
        """
        return (self.start_time < other.end_time and 
                self.end_time > other.start_time)
    
    def __str__(self) -> str:
        """
        Create a readable string representation of the appointment
        This is what gets displayed when we print or show the appointment
        Format: "Title | YYYY-MM-DD HH:MM - HH:MM | Location"
        """
        start_str = self.start_time.strftime("%Y-%m-%d %H:%M")  # Format start time
        end_str = self.end_time.strftime("%H:%M")               # Format end time (same day)
        result = f"{self.title} | {start_str} - {end_str}"      # Basic format
        if self.location:                                       # Add location if it exists
            result += f" | {self.location}"
        return result

# ==================== MAIN SCHEDULING APP CLASS ====================
# This class manages all appointments and provides the main functionality

class SchedulingApp:
    """
    Main application class that manages all scheduling functionality
    This class handles:
    - Storing and managing appointments
    - Saving/loading data to/from files
    - Checking for conflicts
    - Displaying schedules
    """
    def __init__(self, data_file: str = "schedule.json"):
        """
        Initialize the scheduling application
        Args:
            data_file: Name of file to save appointments to (default: schedule.json)
        """
        self.data_file = data_file                    # File where appointments are saved
        self.appointments: List[Appointment] = []     # List to store all appointments in memory
        self.load_appointments()                      # Load any existing appointments from file
    
    def load_appointments(self):
        """
        Load saved appointments from the JSON file into memory
        This runs when the app starts to restore previous appointments
        Handles file not existing or corrupted data gracefully
        """
        if os.path.exists(self.data_file):           # Check if save file exists
            try:
                with open(self.data_file, 'r') as f: # Open file for reading
                    data = json.load(f)              # Parse JSON data from file
                    # Convert each dictionary back into an Appointment object
                    self.appointments = [Appointment.from_dict(apt) for apt in data]
            except (json.JSONDecodeError, KeyError) as e:  # Handle corrupted files
                print(f"Error loading appointments: {e}")
                self.appointments = []               # Start with empty list if file is corrupted
    
    def save_appointments(self):
        """
        Save all current appointments to the JSON file
        This preserves appointments between app sessions
        Called whenever appointments are added or removed
        """
        try:
            # Convert all Appointment objects to dictionaries
            data = [apt.to_dict() for apt in self.appointments]
            with open(self.data_file, 'w') as f:     # Open file for writing
                json.dump(data, f, indent=2)        # Save with nice formatting
        except Exception as e:                       # Handle any file writing errors
            print(f"Error saving appointments: {e}")
    
    def add_appointment(self, title: str, start_time: datetime, end_time: datetime,
                       description: str = "", location: str = "") -> bool:
        """
        Add a new appointment to the schedule
        Includes validation and conflict checking
        
        Args:
            title: Name of the appointment
            start_time: When appointment starts
            end_time: When appointment ends
            description: Optional description
            location: Optional location
        Returns:
            True if appointment was added, False if cancelled
        """
        # Validation: Make sure start time is before end time
        if start_time >= end_time:
            print("Error: Start time must be before end time")
            return False
        
        # Create the new appointment object
        new_appointment = Appointment(title, start_time, end_time, description, location)
        
        # Check if this appointment conflicts with existing ones
        conflicts = self.find_conflicts(new_appointment)
        if conflicts:
            # Warn user about conflicts and let them decide
            print(f"\nWarning: This appointment conflicts with:")
            for conflict in conflicts:
                print(f"  - {conflict}")
            
            # Ask user if they want to proceed despite conflicts
            response = input("\nDo you want to add it anyway? (y/n): ").lower()
            if response != 'y':
                return False  # User cancelled
        
        # Add appointment to our list and save to file
        self.appointments.append(new_appointment)
        self.save_appointments()
        print(f"Appointment '{title}' added successfully!")
        return True
    
    def find_conflicts(self, appointment: Appointment) -> List[Appointment]:
        """
        Find all existing appointments that overlap with the given appointment
        Used for conflict detection when adding new appointments
        
        Args:
            appointment: The appointment to check for conflicts
        Returns:
            List of conflicting appointments (empty if no conflicts)
        """
        conflicts = []
        # Check the new appointment against each existing appointment
        for existing in self.appointments:
            if appointment.overlaps_with(existing):
                conflicts.append(existing)
        return conflicts
    
    def remove_appointment(self, appointment_id: str) -> bool:
        """
        Remove an appointment by its unique ID
        
        Args:
            appointment_id: The unique ID of the appointment to remove
        Returns:
            True if appointment was found and removed, False otherwise
        """
        # Search through all appointments to find the one with matching ID
        for i, apt in enumerate(self.appointments):
            if apt.id == appointment_id:
                removed = self.appointments.pop(i)    # Remove from list
                self.save_appointments()              # Save changes to file
                print(f"Removed appointment: {removed.title}")
                return True
        # If we get here, no appointment with that ID was found
        print("Appointment not found")
        return False
    
    def get_appointments_for_date(self, date: datetime) -> List[Appointment]:
        """
        Get all appointments that occur on a specific date
        
        Args:
            date: The date to get appointments for
        Returns:
            List of appointments on that date
        """
        # Define the start and end of the requested day
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)  # Next day at midnight
        
        # Find appointments that start within this day
        return [apt for apt in self.appointments 
                if start_of_day <= apt.start_time < end_of_day]
    
    def get_upcoming_appointments(self, days: int = 7) -> List[Appointment]:
        """
        Get appointments coming up within the specified number of days
        
        Args:
            days: Number of days to look ahead (default: 7)
        Returns:
            List of upcoming appointments, sorted by start time
        """
        now = datetime.now()                           # Current date/time
        future_date = now + timedelta(days=days)      # End of time range to check
        
        # Find appointments between now and the future date
        upcoming = [apt for apt in self.appointments 
                   if now <= apt.start_time <= future_date]
        # Sort by start time so earliest appointments appear first
        return sorted(upcoming, key=lambda x: x.start_time)
    
    def display_schedule(self, date: datetime = None):
        """
        Display all appointments for a specific date in a nice format
        
        Args:
            date: Date to show schedule for (default: today)
        """
        if date is None:
            date = datetime.now()  # Use today if no date specified
        
        # Get appointments for the requested date
        appointments = self.get_appointments_for_date(date)
        # Sort by start time so they appear chronologically
        appointments.sort(key=lambda x: x.start_time)
        
        # Display header with date and day of week
        print(f"\n=== Schedule for {date.strftime('%Y-%m-%d (%A)')} ===")
        
        if not appointments:
            print("No appointments scheduled")  # Show message if no appointments
        else:
            # Display each appointment with its details
            for apt in appointments:
                # Show ID (first 8 chars), title, time, location
                print(f"[{apt.id[:8]}] {apt}")
                # Show description if it exists
                if apt.description:
                    print(f"    Description: {apt.description}")
                print()  # Empty line for spacing
    
    def display_upcoming(self, days: int = 7):
        """
        Display upcoming appointments grouped by date
        
        Args:
            days: Number of days to look ahead
        """
        upcoming = self.get_upcoming_appointments(days)
        
        print(f"\n=== Upcoming Appointments (Next {days} days) ===")
        
        if not upcoming:
            print("No upcoming appointments")
        else:
            current_date = None  # Track current date to group appointments
            for apt in upcoming:
                apt_date = apt.start_time.date()
                
                # If this is a new date, show a date header
                if apt_date != current_date:
                    current_date = apt_date
                    print(f"\n--- {apt_date.strftime('%Y-%m-%d (%A)')} ---")
                
                # Show appointment with ID for potential removal
                print(f"[{apt.id[:8]}] {apt}")
                if apt.description:
                    print(f"    Description: {apt.description}")

# ==================== UTILITY FUNCTIONS ====================
# Helper functions used by the main application

def parse_datetime(date_str: str, time_str: str) -> datetime:
    """
    Parse user-entered date and time strings into a datetime object
    Handles multiple date formats to be user-friendly
    
    Args:
        date_str: Date as string (e.g., "2025-09-20", "09/20/2025")
        time_str: Time as string (e.g., "14:30", "2:30 PM")
    Returns:
        datetime object combining the date and time
    Raises:
        ValueError if the date/time format is invalid
    """
    try:
        # Try different date formats to be flexible with user input
        for date_fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
            try:
                date_obj = datetime.strptime(date_str, date_fmt).date()
                break  # Found a format that works
            except ValueError:
                continue  # Try next format
        else:
            # None of the formats worked
            raise ValueError("Invalid date format")
        
        # Handle time format (currently only supports 24-hour format)
        time_obj = datetime.strptime(time_str, '%H:%M').time()
        
        # Combine date and time into a single datetime object
        return datetime.combine(date_obj, time_obj)
    except ValueError as e:
        raise ValueError(f"Error parsing date/time: {e}")

# ==================== MAIN PROGRAM / USER INTERFACE ====================
# This is the command-line interface that users interact with

def main():
    app = SchedulingApp()
    
    print("=== Personal Scheduling App ===")
    print("Commands: add, remove, today, date, upcoming, quit")
    
    while True:
        try:
            command = input("\nEnter command: ").lower().strip()
            
            if command == 'quit' or command == 'q':
                print("Goodbye!")
                break
            
            elif command == 'add':
                print("\n--- Add New Appointment ---")
                title = input("Title: ").strip()
                if not title:
                    print("Title cannot be empty")
                    continue
                
                date_str = input("Date (YYYY-MM-DD): ").strip()
                start_time_str = input("Start time (HH:MM): ").strip()
                end_time_str = input("End time (HH:MM): ").strip()
                
                try:
                    start_time = parse_datetime(date_str, start_time_str)
                    end_time = parse_datetime(date_str, end_time_str)
                except ValueError as e:
                    print(f"Error: {e}")
                    continue
                
                description = input("Description (optional): ").strip()
                location = input("Location (optional): ").strip()
                
                app.add_appointment(title, start_time, end_time, description, location)
            
            elif command == 'remove':
                print("\n--- Remove Appointment ---")
                app.display_upcoming(30)  # Show more appointments for removal
                apt_id = input("\nEnter appointment ID (first 8 characters): ").strip()
                
                # Find full ID from partial ID
                full_id = None
                for apt in app.appointments:
                    if apt.id.startswith(apt_id):
                        full_id = apt.id
                        break
                
                if full_id:
                    app.remove_appointment(full_id)
                else:
                    print("Appointment not found")
            
            elif command == 'today':
                app.display_schedule()
            
            elif command == 'date':
                date_str = input("Enter date (YYYY-MM-DD): ").strip()
                try:
                    date = datetime.strptime(date_str, '%Y-%m-%d')
                    app.display_schedule(date)
                except ValueError:
                    print("Invalid date format. Use YYYY-MM-DD")
            
            elif command == 'upcoming':
                try:
                    days = input("Number of days to look ahead (default 7): ").strip()
                    days = int(days) if days else 7
                    app.display_upcoming(days)
                except ValueError:
                    print("Invalid number of days")
            
            elif command == 'help':
                print("\nAvailable commands:")
                print("  add      - Add a new appointment")
                print("  remove   - Remove an appointment")
                print("  today    - Show today's schedule")
                print("  date     - Show schedule for specific date")
                print("  upcoming - Show upcoming appointments")
                print("  help     - Show this help message")
                print("  quit     - Exit the application")
            
            else:
                print("Unknown command. Type 'help' for available commands.")
        
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
