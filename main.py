import flet as ft
import requests
import random
import urllib.parse
from datetime import datetime
import threading
import os

def main(page: ft.Page):
    # ==========================================================
    # CONFIGURAÇÕES BÁSICAS PARA MOBILE
    # ==========================================================
    page.title = "OmniMarket POS"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#F0F4F8"
    page.padding = 0

    hf = ft.HapticFeedback()
    page.overlay.append(hf)
    
    URL = "https://vjytmsiicmmfynlolxrn.supabase.co"
    KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZqeXRtc2lpY21tZnlubG9seHJuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTM4MjI2MTUsImV4cCI6MjEwOTM5ODYxNX0.aavTQjTgsAK94cxWSxRoiMHAzg9f2EpCURgu9IVc6wI"
    HEADERS = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}

    def show_msg(texto, cor):
        page.snack_bar = ft.SnackBar(ft.Text(texto, size=16, color="white"), bgcolor=cor)
        page.snack_bar.open = True
        page.update()

    # ==========================================================
    # ABA INVENTÁRIO (SIMPLIFICADA)
    # ==========================================================
    lista_produtos = ft.ListView(expand=True, spacing=10, padding=10)
    busca_input = ft.TextField(label="Search Code", expand=True, border_color="#334E68")

    def carregar_estoque(e=None):
        lista_produtos.controls.clear()
        lista_produtos.controls.append(ft.Text("Loading...", color="gray", text_align=ft.TextAlign.CENTER))
        page.update()
        try:
            resp = requests.get(f"{URL}/rest/v1/produtos?select=*&limit=30", headers=HEADERS, timeout=5)
            produtos = resp.json()
            lista_produtos.controls.clear()
            for p in produtos:
                lista_produtos.controls.append(
                    ft.Card(content=ft.Container(padding=15, content=ft.Column([
                        ft.Text(p.get('nome', ''), weight=ft.FontWeight.BOLD, size=16),
                        ft.Text(f"$ {float(p.get('preco', 0)):.2f} | Stock: {p.get('estoque', 0)}", color="#334E68")
                    ]))))
        except Exception:
            lista_produtos.controls.clear()
            lista_produtos.controls.append(ft.Text("Connection Error", color="red"))
        page.update()

    view_estoque = ft.Column([
        ft.Container(content=ft.Text("OmniMarket POS", size=24, weight=ft.FontWeight.BOLD, color="white"), bgcolor="#0B3954", padding=10, width=float('inf')),
        ft.Row([busca_input, ft.IconButton(ft.icons.SEARCH, on_click=carregar_estoque)]),
        lista_produtos
    ], expand=True, visible=True)

    # ==========================================================
    # ABA CADASTRO (SIMPLIFICADA)
    # ==========================================================
    cad_cod = ft.TextField(label="Barcode", keyboard_type=ft.KeyboardType.NUMBER)
    cad_nome = ft.TextField(label="Product Name")
    cad_preco = ft.TextField(label="Price ($)", keyboard_type=ft.KeyboardType.NUMBER)

    def salvar_produto(e):
        if not cad_nome.value: return show_msg("Name is required", "red")
        try:
            dados = {"codigo": cad_cod.value or str(random.randint(1000,9999)), "nome": cad_nome.value, "preco": float(cad_preco.value or 0)}
            requests.post(f"{URL}/rest/v1/produtos", headers=HEADERS, json=dados, timeout=5)
            show_msg("Saved!", "green")
            cad_cod.value = ""; cad_nome.value = ""; cad_preco.value = ""
            page.update()
        except: show_msg("Error saving", "red")

    view_cadastrar = ft.Column([
        ft.Container(content=ft.Text("Register Product", size=20, color="white"), bgcolor="#0B3954", padding=10, width=float('inf')),
        ft.Container(content=ft.Column([cad_cod, cad_nome, cad_preco, ft.ElevatedButton("Save", on_click=salvar_produto, bgcolor="green", color="white")]), padding=20)
    ], expand=True, visible=False)

    # ==========================================================
    # NAVEGAÇÃO
    # ==========================================================
    def mudar_aba(e):
        view_estoque.visible = (e.control.selected_index == 0)
        view_cadastrar.visible = (e.control.selected_index == 1)
        if e.control.selected_index == 0: carregar_estoque()
        page.update()

    page.navigation_bar = ft.NavigationBar(
        selected_index=0, on_change=mudar_aba,
        destinations=[
            ft.NavigationDestination(icon=ft.icons.INVENTORY, label="Inventory"),
            ft.NavigationDestination(icon=ft.icons.ADD_BOX, label="Register"),
        ]
    )
    page.add(view_estoque, view_cadastrar)
    carregar_estoque()

if __name__ == "__main__":
    ft.app(target=main)
