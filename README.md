# PDF Dark Mode Viewer

A small Python desktop application for reading PDF documents with an inverted colour scheme. Pages are rendered locally with PyMuPDF and displayed through a Tkinter interface.

## Features

* Open and render PDF files locally
* Navigate between pages
* Scroll pages larger than the application window
* Invert page colours for comfortable low-light reading
* Export the converted pages as a new PDF

## Requirements

* Python 3.9 or later
* Tkinter, normally included with standard Python installations
* PyMuPDF
* Pillow

## Installation

```bash
git clone https://github.com/ibrra3/PDF-DARK-MODE.git
cd PDF-DARK-MODE
python -m venv .venv
```

Activate the environment and install the dependencies:

```bash
pip install -r requirements.txt
```

## Run

```bash
python DarkReader.py
```

## Project status

This is a compact desktop utility and learning project. It currently processes pages in memory, so very large PDFs can require substantial RAM.

