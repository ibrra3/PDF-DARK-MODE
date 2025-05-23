
import fitz  # PyMuPDF
from PIL import Image, ImageOps, ImageTk
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import io  # For saving PDF with PNG image data

class PDFDarkModeApp:
    def __init__(self, master):
        self.master = master
        master.title("PDF Dark Mode Viewer")
        # Set a minimum size for the window
        master.minsize(600, 400)

        self.pdf_path = ""
        self.current_page = 0
        self.doc = None
        self.inverted_pil_images = []  # Store original PIL Images (for saving)
        self.inverted_photo_images = [] # Store Tkinter PhotoImages (for display)
        self.pdf_renderer_instance = None # Store PdfRenderer for Android (not used in this desktop version)


        # --- UI Elements ---

        # Style for ttk widgets
        style = ttk.Style()
        style.theme_use('clam') # You can try other themes: 'alt', 'default', 'classic', 'vista', 'xpnative'


        # File Selection Frame
        self.file_frame = ttk.Frame(master, padding="10")
        self.file_frame.pack(fill=tk.X)

        self.file_label = ttk.Label(self.file_frame, text="No file selected",_style="TLabel")
        self.file_label.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.open_button = ttk.Button(self.file_frame, text="Open PDF", command=self.open_pdf,_style="TButton")
        self.open_button.pack(side=tk.RIGHT, padx=5)

        # Image Display Frame (Canvas for scrolling)
        self.canvas_frame = ttk.Frame(master)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.canvas = tk.Canvas(self.canvas_frame, bg="gray70") # A slightly lighter gray for canvas background
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar_y = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.scrollbar_x = ttk.Scrollbar(master, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X, padx=10)

        self.canvas.configure(yscrollcommand=self.scrollbar_y.set, xscrollcommand=self.scrollbar_x.set)
        self.canvas.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))


        # Navigation Frame
        self.nav_frame = ttk.Frame(master, padding="5")
        self.nav_frame.pack(fill=tk.X)

        self.prev_button = ttk.Button(self.nav_frame, text="Previous", command=self.prev_page, state=tk.DISABLED,_style="TButton")
        self.prev_button.pack(side=tk.LEFT, padx=10, pady=5)

        self.page_label = ttk.Label(self.nav_frame, text="Page: -/-",_style="TLabel", anchor="center")
        self.page_label.pack(side=tk.LEFT, padx=5, expand=True)

        self.next_button = ttk.Button(self.nav_frame, text="Next", command=self.next_page, state=tk.DISABLED,_style="TButton")
        self.next_button.pack(side=tk.RIGHT, padx=10, pady=5)

        # Save Button Frame
        self.save_frame = ttk.Frame(master, padding="5")
        self.save_frame.pack(fill=tk.X)
        self.save_button = ttk.Button(self.save_frame, text="Save Inverted PDF", command=self.save_inverted_pdf, state=tk.DISABLED,_style="TButton")
        self.save_button.pack(pady=5) # Center the button


    def open_pdf(self):
        """Opens a file dialog and loads the selected PDF."""
        file_path = filedialog.askopenfilename(
            title="Select a PDF File",
            filetypes=[("PDF Files", "*.pdf")]
        )
        if file_path:
            self.pdf_path = file_path
            # Truncate displayed path if too long
            display_path = self.pdf_path
            if len(display_path) > 70: # Adjust length as needed
                display_path = "..." + display_path[-67:]
            self.file_label.config(text=display_path)
            self.load_pdf_document()


    def load_pdf_document(self):
        """Loads the PDF, preprocesses pages, and displays the first page."""
        try:
            if self.doc: # Close previously opened document
                self.doc.close()
                self.doc = None

            self.doc = fitz.open(self.pdf_path)
            self.current_page = 0
            self.inverted_pil_images = []  # Clear previous PIL images
            self.inverted_photo_images = [] # Clear previous PhotoImages

            self.preprocess_all_pages()
            if self.inverted_photo_images: # Check if preprocessing was successful
                self.display_page()
                self.save_button.config(state=tk.NORMAL)
            else:
                 messagebox.showerror("Error", "Could not process any pages from the PDF.")
                 self.reset_ui_on_error()

            self.update_navigation_buttons()

        except Exception as e:
            messagebox.showerror("Error", f"Could not open or process PDF: {e}")
            self.reset_ui_on_error()

    def reset_ui_on_error(self):
        """Resets UI elements in case of an error loading a PDF."""
        self.doc = None
        self.inverted_pil_images = []
        self.inverted_photo_images = []
        self.canvas.delete("all")
        self.file_label.config(text="No file selected")
        self.page_label.config(text="Page: -/-")
        self.prev_button.config(state=tk.DISABLED)
        self.next_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)


    def preprocess_all_pages(self):
        """Inverts colors for all pages and stores them."""
        if not self.doc:
            return

        for page_num in range(len(self.doc)):
            try:
                pil_img, photo_img = self.invert_and_prepare_page(page_num)
                if pil_img and photo_img:
                    self.inverted_pil_images.append(pil_img)
                    self.inverted_photo_images.append(photo_img)
                else: # Add placeholders if a page fails
                    self.inverted_pil_images.append(None)
                    self.inverted_photo_images.append(None)
                    print(f"Warning: Could not process page {page_num + 1}")
            except Exception as e:
                print(f"Error processing page {page_num + 1}: {e}")
                self.inverted_pil_images.append(None)
                self.inverted_photo_images.append(None)


    def invert_and_prepare_page(self, page_number):
        """Inverts the colors of a single PDF page and returns PIL and PhotoImage."""
        page = self.doc.load_page(page_number)
        pix = page.get_pixmap()
        pil_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        inverted_pil_img = ImageOps.invert(pil_img)
        photo_img = ImageTk.PhotoImage(inverted_pil_img)
        return inverted_pil_img, photo_img

    def display_page(self):
        """Displays the current page in the canvas."""
        if self.doc and 0 <= self.current_page < len(self.inverted_photo_images):
            photo = self.inverted_photo_images[self.current_page]
            if photo:
                self.canvas.delete("all")  # Clear previous image
                self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
                self.canvas.image = photo  # Keep a reference!
                # Update scrollregion after image is placed
                self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
                self.page_label.config(text=f"Page: {self.current_page + 1}/{len(self.doc)}")
            else:
                self.canvas.delete("all")
                self.canvas.create_text(self.canvas.winfo_width()/2, self.canvas.winfo_height()/2,
                                       text="Error: Page could not be displayed", fill="red", anchor="center")
                self.page_label.config(text=f"Page: {self.current_page + 1}/{len(self.doc)} (Error)")


    def next_page(self):
        """Moves to the next page."""
        if self.doc and self.current_page < len(self.doc) - 1:
            self.current_page += 1
            self.display_page()
            self.update_navigation_buttons()

    def prev_page(self):
        """Moves to the previous page."""
        if self.doc and self.current_page > 0:
            self.current_page -= 1
            self.display_page()
            self.update_navigation_buttons()

    def update_navigation_buttons(self):
        """Enables/disables navigation buttons based on current page."""
        if not self.doc or not self.inverted_photo_images:
            self.prev_button.config(state=tk.DISABLED)
            self.next_button.config(state=tk.DISABLED)
            return

        total_pages = len(self.doc)
        self.prev_button.config(state=tk.NORMAL if self.current_page > 0 else tk.DISABLED)
        self.next_button.config(state=tk.NORMAL if self.current_page < total_pages - 1 else tk.DISABLED)


    def save_inverted_pdf(self):
        """Saves the inverted PDF to a new file."""
        if not self.doc or not self.inverted_pil_images:
            messagebox.showerror("Error", "No PDF loaded or processed to save.")
            return

        output_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")],
            title="Save Inverted PDF As"
        )

        if output_path:
            try:
                new_doc = fitz.open()  # Create an empty PDF for saving

                for page_num in range(len(self.doc)):
                    pil_img_to_save = self.inverted_pil_images[page_num]

                    if pil_img_to_save:
                        original_page_for_dims = self.doc.load_page(page_num)
                        rect = original_page_for_dims.rect

                        # Save PIL Image to a BytesIO object as PNG
                        img_byte_arr = io.BytesIO()
                        pil_img_to_save.save(img_byte_arr, format='PNG')
                        img_byte_arr.seek(0)  # Rewind to the beginning of the stream

                        # Create a new page in the output PDF and insert the image
                        new_page = new_doc.new_page(width=rect.width, height=rect.height)
                        new_page.insert_image(rect, stream=img_byte_arr)
                    else:
                        # Optionally, add a blank page or a message page for failed pages
                        new_page = new_doc.new_page(width=self.doc[0].rect.width, height=self.doc[0].rect.height) # Use first page dims
                        new_page.insert_text((50, 50), f"Page {page_num + 1} could not be processed.")
                        print(f"Warning: Skipping page {page_num + 1} in saved PDF due to processing error.")


                new_doc.save(output_path)
                new_doc.close()
                messagebox.showinfo("Success", f"Inverted PDF saved to {output_path}")

            except Exception as e:
                messagebox.showerror("Error", f"Could not save inverted PDF: {e}")
            finally:
                if 'new_doc' in locals() and new_doc.is_open:
                    new_doc.close()

    def on_closing(self):
        """Handle window closing event."""
        if self.doc:
            self.doc.close()
        self.master.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = PDFDarkModeApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing) # Handle window close button
    root.mainloop()  