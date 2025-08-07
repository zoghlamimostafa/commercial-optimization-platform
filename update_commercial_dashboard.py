import re

# Path to the HTML file
html_file_path = r'c:\Users\mostafa zoghlami\Desktop\souha\templates\commercial_dashboard.html'

# Read the current content of the file
with open(html_file_path, 'r', encoding='utf-8') as file:
    content = file.read()

# Replace the title in the <title> tag
content = re.sub(
    r'<title>Dashboard Commercial \{\{ commercial_code \}\}</title>',
    r'<title>Dashboard {{ commercial_name }}</title>',
    content
)

# Replace in the breadcrumb
content = re.sub(
    r'<li class="breadcrumb-item active">Commercial \{\{ commercial_code \}\}</li>',
    r'<li class="breadcrumb-item active">{{ commercial_name }} (Code: {{ commercial_code }})</li>',
    content
)

# Replace in the header
content = re.sub(
    r'<h2><i class="fas fa-user-tie me-2"></i>Commercial \{\{ commercial_code \}\}</h2>',
    r'<h2><i class="fas fa-user-tie me-2"></i>{{ commercial_name }}</h2>\n                            <p class="text-white mb-0">Code: {{ commercial_code }}</p>',
    content
)

# Replace in the chart titles and texts
content = re.sub(
    r"title: 'Dashboard Commercial \{\{ commercial_code \}\}'",
    r"title: 'Dashboard {{ commercial_name }}'",
    content
)

content = re.sub(
    r"text: 'Consultez les performances du commercial \{\{ commercial_code \}\}'",
    r"text: 'Consultez les performances de {{ commercial_name }} (Code: {{ commercial_code }})'",
    content
)

# Write the modified content back to the file
with open(html_file_path, 'w', encoding='utf-8') as file:
    file.write(content)

print("Commercial dashboard template updated successfully!")
