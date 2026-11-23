import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

BG='#f7f4f5'; BURGUNDY='#70213d'

class RestaurantApp(tk.Tk):
    def __init__(self, controller):
        super().__init__()
        self.controller=controller
        self.title('Group12 | Restaurant Order Management System')
        self.geometry('1130x750')
        self.minsize(900,600)
        self.configure(bg=BG)
        self.selected_order=None
        style=ttk.Style(self)
        style.theme_use('clam')
        style.configure('Treeview',rowheight=30,font=('Segoe UI',10))
        style.configure('Treeview.Heading',font=('Segoe UI',10,'bold'))
        self.login_page()

    def clear(self):
        for w in self.winfo_children(): w.destroy()

    def label(self, parent, text, size=11, bold=False):
        return tk.Label(parent,text=text,bg=BG,fg='#222',font=('Segoe UI',size,'bold' if bold else 'normal'))

    def btn(self, parent, text, command):
        return tk.Button(parent,text=text,command=command,bg=BURGUNDY,fg='white',font=('Segoe UI',10,'bold'),relief='flat',padx=12,pady=8)

    def error_safe(self, fn):
        try: fn()
        except Exception as exc: messagebox.showerror('Operation failed',str(exc))

    def login_page(self):
        self.clear()
        panel=tk.Frame(self,bg=BG); panel.pack(expand=True)
        self.label(panel,'RESTAURANT ORDER MANAGEMENT',23,True).pack(pady=12)
        self.label(panel,'Group 12 • Sign in',13).pack(pady=8)
        self.label(panel,'Username').pack(anchor='w')
        username=ttk.Entry(panel,width=38); username.pack(pady=5)
        self.label(panel,'Password').pack(anchor='w')
        password=ttk.Entry(panel,width=38,show='*'); password.pack(pady=5)
        def login():
            if self.controller.sign_in(username.get(),password.get()): self.shell('Tables')
            else: messagebox.showerror('Login','Invalid username or password')
        self.btn(panel,'Login',login).pack(fill='x',pady=14)
        self.label(panel,'First run: create an admin password in the console.',10).pack()
        password.bind('<Return>',lambda _:login())

    def shell(self, page):
        self.clear()
        top=tk.Frame(self,bg=BURGUNDY,height=65); top.pack(fill='x')
        tk.Label(top,text='  RESTAURANT ORDER MANAGEMENT  |  GROUP12',fg='white',bg=BURGUNDY,font=('Segoe UI',16,'bold')).pack(side='left',pady=18)
        tk.Button(top,text='Logout',command=self.login_page).pack(side='right',padx=18)
        nav=tk.Frame(self,bg='#eadde2'); nav.pack(fill='x')
        for name in ('Tables','Orders','Kitchen','Menu','Checkout','Reports','Users'):
            if name=='Kitchen' and not self.controller.can('Kitchen'): continue
            if name in ('Orders','Tables') and not self.controller.can('Waiter'): continue
            if name=='Checkout' and not self.controller.can('Cashier'): continue
            if name in ('Menu','Reports','Users') and not self.controller.can(): continue
            tk.Button(nav,text=name,command=lambda n=name:self.shell(n),relief='flat',bg='#eadde2',padx=15,pady=10).pack(side='left')
        self.body=tk.Frame(self,bg=BG,padx=24,pady=20); self.body.pack(fill='both',expand=True)
        self.label(self.body,page,20,True).pack(anchor='w',pady=(0,15))
        getattr(self,'page_'+page.lower())()

    def table(self, columns, rows, height=13):
        tree=ttk.Treeview(self.body,columns=columns,show='headings',height=height)
        for c in columns: tree.heading(c,text=c); tree.column(c,width=155,anchor='w')
        for row in rows: tree.insert('', 'end', values=row)
        tree.pack(fill='both',expand=True,pady=8)
        return tree

    def selected_id(self, tree):
        selection=tree.selection()
        if not selection: raise ValueError('Select a row first')
        return int(tree.item(selection[0])['values'][0])

    def page_tables(self):
        s=self.controller.service
        tree=self.table(('ID','Table','Status'),[(x['id'],x['name'],x['status']) for x in s.tables()])
        def create():
            order=s.create_order(self.selected_id(tree))
            messagebox.showinfo('New order',f'Order #{order} created')
            self.shell('Orders')
        self.btn(self.body,'Create order for selected available table',lambda:self.error_safe(create)).pack(anchor='w')

    def page_orders(self):
        s=self.controller.service
        tree=self.table(('Order ID','Table','Created'),[(x['id'],x['table_name'],x['created_at']) for x in s.active_orders()],6)
        controls=tk.Frame(self.body,bg=BG); controls.pack(fill='x',pady=8)
        self.label(controls,'Menu item').pack(side='left')
        menu=s.menu(); lookup={f"{x['name']} – {x['price']:,} VND":x['id'] for x in menu}
        choice=ttk.Combobox(controls,values=list(lookup),width=38,state='readonly'); choice.pack(side='left',padx=8)
        if lookup: choice.current(0)
        self.label(controls,'Qty').pack(side='left')
        qty=ttk.Spinbox(controls,from_=1,to=100,width=5); qty.set(1); qty.pack(side='left',padx=5)
        self.label(controls,'Note').pack(side='left')
        note=ttk.Entry(controls,width=20); note.pack(side='left',padx=5)
        def add():
            if not choice.get(): raise ValueError('Select a menu item')
            s.add_item(self.selected_id(tree),lookup[choice.get()],qty.get(),note.get())
            self.shell('Orders')
        self.btn(controls,'Add dish',lambda:self.error_safe(add)).pack(side='left',padx=5)
        self.label(self.body,'Selected order details (select an order, then click View)').pack(anchor='w')
        detail_frame=tk.Frame(self.body,bg=BG); detail_frame.pack(fill='both',expand=True)
        def view():
            order=self.selected_id(tree)
            for w in detail_frame.winfo_children(): w.destroy()
            d=ttk.Treeview(detail_frame,columns=('ID','Dish','Qty','Price','Status','Note'),show='headings',height=6)
            for c in ('ID','Dish','Qty','Price','Status','Note'): d.heading(c,text=c); d.column(c,width=115)
            for x in s.details(order): d.insert('','end',values=(x['id'],x['item_name'],x['quantity'],x['unit_price'],x['status'],x['note']))
            d.pack(fill='x')
            self.label(detail_frame,f'Subtotal: {s.total(order):,} VND',13,True).pack(anchor='w',pady=5)
            def remove(): s.remove_item(self.selected_id(d)); view()
            def change():
                q=simpledialog.askinteger('Quantity','New quantity:',minvalue=1,parent=self)
                if q is not None: s.update_quantity(self.selected_id(d),q); view()
            self.btn(detail_frame,'Update quantity',lambda:self.error_safe(change)).pack(side='left',padx=4)
            self.btn(detail_frame,'Remove pending dish',lambda:self.error_safe(remove)).pack(side='left',padx=4)
        self.btn(self.body,'View selected order',lambda:self.error_safe(view)).pack(anchor='w',pady=5)

    def page_kitchen(self):
        s=self.controller.service
        tree=self.table(('Detail ID','Table','Dish','Qty','Notes','Status'),[(x['id'],x['table_name'],x['item_name'],x['quantity'],x['note'],x['status']) for x in s.kitchen_items()])
        def next_status():
            row=s.db.one('SELECT status FROM order_details WHERE id=?',(self.selected_id(tree),))
            target={'Pending':'Cooking','Cooking':'Ready'}.get(row['status']) if row else None
            if not target: raise ValueError('Dish is already ready')
            s.set_kitchen_status(self.selected_id(tree),target); self.shell('Kitchen')
        self.btn(self.body,'Advance selected dish: Pending → Cooking → Ready',lambda:self.error_safe(next_status)).pack(anchor='w')

    def page_menu(self):
        s=self.controller.service
        tree=self.table(('ID','Dish','Category','Price VND','Available'),[(x['id'],x['name'],x['category'],x['price'],x['available']) for x in s.menu(True)])
        def prompt(existing=None):
            name=simpledialog.askstring('Menu','Dish name:',initialvalue=existing['name'] if existing else '',parent=self)
            if name is None:return
            category=simpledialog.askstring('Menu','Category:',initialvalue=existing['category'] if existing else 'Main Dish',parent=self)
            if category is None:return
            price=simpledialog.askinteger('Menu','Price (VND):',initialvalue=existing['price'] if existing else 50000,minvalue=0,parent=self)
            if price is None:return
            if existing:
                available=messagebox.askyesno('Availability','Is this dish available?')
                s.update_menu_item(existing['id'],name,category,price,available)
            else:s.add_menu_item(name,category,price)
            self.shell('Menu')
        self.btn(self.body,'Add new dish',lambda:self.error_safe(lambda:prompt())).pack(side='left',padx=4)
        def edit():
            item=s.db.one('SELECT * FROM menu_items WHERE id=?',(self.selected_id(tree),))
            prompt(item)
        self.btn(self.body,'Edit selected dish / availability',lambda:self.error_safe(edit)).pack(side='left',padx=4)

    def page_checkout(self):
        s=self.controller.service
        tree=self.table(('Order ID','Table','Subtotal'),[(x['id'],x['table_name'],s.total(x['id'])) for x in s.active_orders()])
        controls=tk.Frame(self.body,bg=BG); controls.pack(anchor='w',pady=10)
        self.label(controls,'Payment method').pack(side='left')
        method=ttk.Combobox(controls,values=('Cash','Card','QR'),state='readonly',width=12); method.current(0); method.pack(side='left',padx=10)
        self.label(controls,'Discount VND').pack(side='left')
        discount=ttk.Entry(controls,width=12); discount.insert(0,'0'); discount.pack(side='left',padx=10)
        def pay():
            oid=self.selected_id(tree)
            if not messagebox.askyesno('Confirm payment',f'Confirm payment for order #{oid}?'): return
            amount=s.checkout(oid,method.get(),discount.get())
            messagebox.showinfo('Receipt',f'Order #{oid} paid successfully\nMethod: {method.get()}\nTotal: {amount:,} VND')
            self.shell('Checkout')
        self.btn(self.body,'Confirm payment and clear table',lambda:self.error_safe(pay)).pack(anchor='w')
        self.label(self.body,'All dishes must be marked Ready by the kitchen before payment.',10).pack(anchor='w',pady=10)

    def page_reports(self):
        report=self.controller.service.report()
        self.label(self.body,f"Paid orders: {report['orders']}",16,True).pack(anchor='w',pady=10)
        self.label(self.body,f"Total revenue: {report['revenue']:,} VND",16,True).pack(anchor='w',pady=10)
        self.label(self.body,'Figures reflect all paid orders in the local database.',10).pack(anchor='w')

    def page_users(self):
        s=self.controller.service
        self.table(('ID','Username','Role'),[(x['id'],x['username'],x['role']) for x in s.db.all('SELECT id,username,role FROM users')])
        def add():
            username=simpledialog.askstring('User','New username:',parent=self)
            if not username:return
            password=simpledialog.askstring('User','Password (at least 8 characters):',show='*',parent=self)
            if password is None:return
            role=simpledialog.askstring('User','Role: Manager, Waiter, Kitchen, Cashier',parent=self)
            if role is None:return
            s.create_user(username,password,role); self.shell('Users')
        self.btn(self.body,'Create staff account',lambda:self.error_safe(add)).pack(anchor='w')
