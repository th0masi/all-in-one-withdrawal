import tkinter as tk
import tkinter.ttk as ttk
import webbrowser
import threading

from tkinter import filedialog
from tkinter import messagebox
from ttkbootstrap import Style
from modules.ubils import *


class WithdrawalApp:
    def __init__(self):
        self.network_data = {}
        self.token = ''
        self.networks = []
        self.addresses = []
        self.is_file_selected = False
        self.build_gui()

    def load_wallets(self):
        filename = filedialog.askopenfilename()

        if filename:
            with open(filename, "r") as file:
                self.addresses = [line.strip() for line in file if line.strip()]
            self.addresses_label['text'] = f"Loaded {len(self.addresses)} wallets"
            self.is_file_selected = True
            self.check_run_button()
        else:
            if not self.is_file_selected:
                self.addresses_label['text'] = f"No file selected"

    def shuffle_addresses(self, *args):
        if self.addresses and self.shuffle_var.get():
            random.shuffle(self.addresses)

    def on_button_click(self):
        self.token = self.entry.get()

        exchange_function_name = f"{self.exchange_var.get().lower()}_get_withdrawal_info"
        exchange_function = globals().get(exchange_function_name)

        if not exchange_function:
            print(f"No such function: {exchange_function_name}")
            return

        self.networks, self.network_data = exchange_function(self.token)

        menu = self.optionmenu['menu']
        menu.delete(0, 'end')

        for network in self.networks:
            display_network = network[:12] + '...' if len(network) > 12 else network
            menu.add_command(label=display_network, command=lambda n=network: self.optionmenu_var.set(n))

        if self.networks:
            self.optionmenu_var.set(self.networks[0])
            self.show_fee_for_network()

    def show_fee_for_network(self):
        network = self.optionmenu_var.get()
        if network != 'Select chain..':
            network_info = self.network_data.get(network)
            if network_info is not None:
                id, fee, min_withdrawal = network_info
                self.fee_label.config(text=f"Fee: {fee}  |  Min withdrawal: {min_withdrawal}")
            else:
                print(f"No information available for network {network}")
        else:
            pass

    def run(self):
        self.shuffle_addresses()
        def thread_task():
            withdrawal_range = (float(self.min_amount.get().replace(',', '.')), float(self.max_amount.get().replace(',', '.')))
            selected_network = self.optionmenu_var.get()
            selected_exchange = self.exchange_var.get().lower()
            network_id, fee, min_withdraw = self.network_data[selected_network] if selected_network in self.network_data else ("Unknown", "None")
            success_counter = 0

            print(f"\n ---NEW WITHDRAW CONFIGURATION ---")
            print(f"Soft by th0masi: https://t.me/thor_lab")
            print(f"Selected Exchange: {selected_exchange.capitalize()}")
            print(f"Amount Range: {withdrawal_range}")
            print(f"Delay Range: {(float(self.min_delay_var.get()), float(self.max_delay_var.get()))}")
            print(f"Network ID: {network_id}")
            print(f"Token: {self.token}")
            print(f"Wallet Addresses: {self.addresses}")

            for address in self.addresses:
                amount = smart_round(random.uniform(*withdrawal_range))
                try:
                    func = globals()[f"{selected_exchange}_withdraw"]
                    if selected_exchange == "okx":
                        success = func(address, amount, self.token, network_id, fee)
                    else:
                        success = func(address, amount, self.token, network_id)
                    if success:
                        success_counter += 1
                        self.window.after(0, lambda: self.status_label.config(text=f"Successfully withdrawn to {success_counter}/{len(self.addresses)} addresses"))
                    else:
                        self.window.after(0, lambda: self.status_label.config(text=f"Failed to withdraw to {address}"))

                except Exception as e:
                    print(f"Error when withdrawing to {address}: {str(e)}")
                    self.window.after(0, lambda: self.status_label.config(text=f"Error when withdrawing to {address}: {str(e)}"))

                delay = random.uniform(float(self.min_delay_var.get()), float(self.max_delay_var.get()))
                time.sleep(delay)

            print(f"\n>>>  Withdrawn to {success_counter} out of {len(self.addresses)} addresses")
            if success_counter == len(self.addresses):
                print("\n>>>  Withdrawn to all addresses")
                self.window.after(0, lambda: self.status_label.config(text="Withdrawn to all addresses"))
                self.window.after(0, lambda: messagebox.showinfo("Withdrawal Completed", "Withdrawn to all addresses"))
            else:
                self.window.after(0, lambda: self.status_label.config(text=f"Withdrawn to {success_counter} out of {len(self.addresses)} addresses"))
                self.window.after(0, lambda: messagebox.showinfo("Withdrawal Completed", f"Withdrawn to {success_counter} out of {len(self.addresses)} addresses"))

            self.window.after(0, lambda: self.window.iconify())

        thread = threading.Thread(target=thread_task)
        thread.start()

    def activate_block(self, *args):
        if self.exchange_var.get():
            self.entry.config(state="normal")
            self.button.config(state="normal")
            self.optionmenu.config(state='normal')
            self.max_delay_time.config(state='normal')
            self.min_delay_time.config(state='normal')
            self.load_wallets_button.config(state="normal")
            self.min_amount.config(state="normal")
            self.max_amount.config(state="normal")

            self.entry.delete(0, 'end')
            self.token = ''
            self.networks = []
            self.network_data = {}
            self.optionmenu_var.set('Select chain..')
            menu = self.optionmenu['menu']
            menu.delete(0, 'end')
            self.fee_label.config(text="")
        else:
            self.entry.config(state="disabled")
            self.button.config(state="disabled")
            self.optionmenu.config(state='disabled')
            self.max_delay_time.config(state='disabled')
            self.min_delay_time.config(state='disabled')

    def check_run_button(self):
        if self.addresses and self.token and self.optionmenu_var.get() and self.min_amount_var.get() and self.max_amount_var.get() and self.min_delay_var.get() and self.max_delay_var.get():
            self.block_run_button.config(state="normal")
        else:
            self.block_run_button.config(state="disabled")

    def build_gui(self):
        # GUI setup
        self.window = tk.Tk()
        style = Style('superhero')
        self.window = style.master
        self.window.geometry("520x710")
        self.window.title("all-in-one withdraw cex")

        self.min_amount_var = tk.StringVar()
        self.max_amount_var = tk.StringVar()
        self.optionmenu_var = tk.StringVar()
        self.optionmenu_var.trace("w", lambda name, index, mode: self.show_fee_for_network())
        self.min_delay_var = tk.StringVar()
        self.max_delay_var = tk.StringVar()
        self.exchange_var = tk.StringVar()
        self.shuffle_var = tk.BooleanVar()
        self.shuffle_var.trace('w', self.shuffle_addresses)

        self.exchanges = ['OKX', 'Binance', 'Mexc', 'Kucoin', 'Huobi', 'Gate', 'Bitget']
        self.main_frame = ttk.Frame(self.window, padding=20)
        self.main_frame.pack(fill='both', expand=True)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure("all", weight=1)

        # Select exchange
        block_select_exchange = ttk.LabelFrame(self.main_frame, text="Exchange selection", padding=20)
        block_select_exchange.grid(row=1, column=0, padx=5, pady=5, sticky='ew', columnspan=3)

        for i, exchange in enumerate(self.exchanges):
            ttk.Radiobutton(block_select_exchange, text=exchange, value=exchange, variable=self.exchange_var).grid(row=0, column=i, padx=5, pady=5)

        self.exchange_var.trace("w", self.activate_block)

        # Token selection
        block_token = ttk.LabelFrame(self.main_frame, text="Token selection", padding=20)
        block_token.grid(row=2, column=0, padx=5, pady=5, sticky='ew', columnspan=3)

        self.entry = ttk.Entry(block_token, state="disabled")
        self.entry.grid(row=0, column=0, padx=5, pady=5)

        self.button = ttk.Button(block_token, text="Get info", command=self.on_button_click, state="disabled")
        self.button.grid(row=0, column=1, padx=5, pady=5)

        self.optionmenu = ttk.OptionMenu(block_token, self.optionmenu_var, 'Select chain..')
        self.optionmenu.config(state='disabled', width=15)
        self.optionmenu.grid(row=0, column=2, padx=5, pady=5)

        self.fee_label = ttk.Label(block_token, text="")
        self.fee_label.grid(row=1, column=0, columnspan=3, padx=5, pady=(5, 0))

        # Wallets load
        block_wallets = ttk.LabelFrame(self.main_frame, text="Wallets", padding=20)
        block_wallets.grid(row=3, column=0, padx=5, pady=5, sticky='ew', columnspan=3)

        self.load_wallets_button = ttk.Button(block_wallets, text="Load wallets", command=self.load_wallets, state="disabled")
        self.load_wallets_button.grid(row=0, column=0, padx=5, pady=5)

        self.addresses_label = ttk.Label(block_wallets, text="")
        self.addresses_label.grid(row=0, column=1, padx=5, pady=5)

        self.shuffle_checkbutton = ttk.Checkbutton(block_wallets, text="Shuffle wallets", variable=self.shuffle_var)
        self.shuffle_checkbutton.grid(row=2, column=0, padx=(7, 0), pady=(10, 0))

        # Withdrawal amount
        block_withdraw_amount = ttk.LabelFrame(self.main_frame, text="Withdrawal amount", padding=20)
        block_withdraw_amount.grid(row=4, column=0, padx=5, pady=5, sticky='ew', columnspan=3)

        from_label = ttk.Label(block_withdraw_amount, text="from", font=('Arial', 9))
        from_label.grid(row=0, column=0, padx=5, pady=5)

        self.min_amount = ttk.Entry(block_withdraw_amount, textvariable=self.min_amount_var, font=('Arial', 10),
                                    width=8, state="disabled")
        self.min_amount.grid(row=0, column=1, padx=5, pady=5)

        to_label = ttk.Label(block_withdraw_amount, text="to", font=('Arial', 9))
        to_label.grid(row=0, column=2, padx=5, pady=5)

        self.max_amount = ttk.Entry(block_withdraw_amount, textvariable=self.max_amount_var, font=('Arial', 10),
                                    width=8, state="disabled")
        self.max_amount.grid(row=0, column=3, padx=5, pady=5)

        # Delay between wallets
        block_delay = ttk.LabelFrame(self.main_frame, text="Delay between wallets (s)", padding=20)
        block_delay.grid(row=5, column=0, padx=5, pady=5, sticky='ew', columnspan=3)

        from_delay_label = ttk.Label(block_delay, text="from", font=('Arial', 9))
        from_delay_label.grid(row=0, column=0, padx=5, pady=5)

        self.min_delay_time = ttk.Entry(block_delay, textvariable=self.min_delay_var, font=('Arial', 10), width=8,
                                        state="disabled")
        self.min_delay_time.grid(row=0, column=1, padx=5, pady=5)

        to_delay_label = ttk.Label(block_delay, text="to", font=('Arial', 9))
        to_delay_label.grid(row=0, column=2, padx=5, pady=5)

        self.max_delay_time = ttk.Entry(block_delay, textvariable=self.max_delay_var, font=('Arial', 10), width=8,
                                        state="disabled")
        self.max_delay_time.grid(row=0, column=3, padx=5, pady=5)

        # Bindings
        self.min_amount_var.trace('w', lambda *args: self.check_run_button())
        self.max_amount_var.trace('w', lambda *args: self.check_run_button())
        self.min_delay_var.trace('w', lambda *args: self.check_run_button())
        self.max_delay_var.trace('w', lambda *args: self.check_run_button())
        self.optionmenu_var.trace('w', lambda *args: self.check_run_button())

        # Run button
        self.block_run_button = ttk.Button(self.main_frame, text="Start Withdrawal", command=self.run, state="disabled")
        self.block_run_button.grid(row=6, column=0, padx=5, pady=5, sticky='ew', columnspan=3)

        # Status message
        block_status = ttk.Frame(self.main_frame, padding=5)
        block_status.grid(row=7, column=0, padx=5, pady=5, sticky='ew', columnspan=3)

        self.status_label = ttk.Label(block_status, text="")
        self.status_label.grid(row=0, column=0, padx=0, pady=5)

        # Powered by
        block_powered_by = tk.Frame(self.main_frame)
        block_powered_by.grid(row=0, column=0, pady=(0, 8), sticky='ew', columnspan=3)

        style.configure('Custom.TLabel', foreground='#97a9a5')
        link_label = ttk.Label(block_powered_by, text="Powered by ThorLab", style='Custom.TLabel', cursor="hand2")
        link_label.grid(row=0, column=1)  # Note that the column is now 1
        link_label.bind("<Button-1>", lambda e: webbrowser.open_new("https://t.me/thor_lab"))

        github_label = ttk.Label(block_powered_by, text=" [github.com/th0masi] ", style='Custom.TLabel', cursor="hand2")
        github_label.grid(row=0, column=2)
        github_label.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com/th0masi"))

        empty_label_left = ttk.Label(block_powered_by, text="")
        empty_label_left.grid(row=0, column=0, sticky='ew')

        empty_label_right = ttk.Label(block_powered_by, text="")
        empty_label_right.grid(row=0, column=3, sticky='ew')

        block_powered_by.grid_columnconfigure(0, weight=1)
        block_powered_by.grid_columnconfigure(3, weight=1)

        # Bindings
        self.min_amount_var.trace('w', lambda *args: self.check_run_button())
        self.max_amount_var.trace('w', lambda *args: self.check_run_button())
        self.min_delay_var.trace('w', lambda *args: self.check_run_button())
        self.max_delay_var.trace('w', lambda *args: self.check_run_button())
        self.optionmenu_var.trace('w', lambda *args: self.check_run_button())

    def run_app(self):
        self.window.mainloop()


if __name__ == "__main__":
    app = WithdrawalApp()
    app.run_app()
