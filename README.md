# 🎓 EduLearn Pro

**EduLearn Pro** is a fully functional, two-sided Learning Management System (LMS) built with Python and Flask. It empowers instructors to create courses and upload lessons, while providing students with an intuitive platform to discover content, enroll in courses, and track their learning progress.

---

##  Key Features

### For Instructors
* **Course Creation:** Easily create and manage courses with custom thumbnails and descriptions.
* **Lesson Management:** Add structured lessons featuring rich text descriptions and embedded video content (supports dynamic YouTube embeds and external links).
* **Instructor Dashboard:** A dedicated hub to view, edit, and manage all authored courses.

### For Students
* **Course Catalog & Search:** Browse available courses or use the SQL-powered search bar to find specific topics.
* **One-Click Enrollment:** Seamlessly enroll in courses to add them to your personal learning library.
* **Progress Tracking:** Mark lessons as "Complete" and watch your progress bar fill up as you advance through the course.
* **Student Dashboard:** A personalized space to access enrolled courses and resume learning.

### Core System Features
* **Secure Authentication:** User registration and login system with secure password hashing.
* **Role-Based Access Control:** Distinct experiences and permissions for 'Student' and 'Instructor' accounts.
* **User Profiles:** Customizable profiles with dynamic avatar/profile picture uploads.
* **Relational Database:** Powered by SQLite with a robust schema connecting Users, Courses, Lessons, Enrollments, and Progress.

---

## Tech Stack

* **Backend:** Python 3, Flask, Jinja2
* **Database:** SQLite3
* **Frontend:** HTML5, CSS3, Bootstrap 5
* **Security:** Werkzeug Security (Password Hashing)

---

## Getting Started

Follow these instructions to get a copy of the project running on your local machine.

### Prerequisites
* Python 3.8+ installed on your system.
* Git installed.

### Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/your-username/EduLearn-Pro.git](https://github.com/your-username/EduLearn-Pro.git)
   cd EduLearn-Pro