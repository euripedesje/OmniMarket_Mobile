import flet as ft
import traceback
import sys

def main(page: ft.Page):
    # =========================================================================
    # 1. IMEDIATAMENTE DESENHAR A INTERFACE (Cura a tela preta)
    # =========================================================================
    page.title = "OmniMarket POS"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#F0F4F8"
    page.padding = 0
    
    # Mostra uma tela de carregamento segura
    msg_carregando = ft.Text("Loading System...", size=20, weight="bold", color="#102A43")
    tela_carregamento = ft.Container(content=msg_carregando, alignment=ft.alignment.center, expand=True)
    page.add(tela_carregamento)
    page.update()

    try:
        # =========================================================================
        # 2. IMPORTAÇÕES MOVIDAS PARA AQUI DENTRO (Se falhar, captura na tela)
        # =========================================================================
        import requests
        import random
        import threading
        import urllib.parse
        from datetime import datetime, timezone, timedelta
        import os

        # =========================================================================
        # CLOUD CREDENTIALS & TIMEZONE (OMNIMARKET POS)
        # =========================================================================
        URL = "https://vjytmsiicmmfynlolxrn.supabase.co"
        KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZqeXRtc2lpY21tZnlubG9seHJuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTM4MjI2MTUsImV4cCI6MjEwOTM5ODYxNX0.aavTQjTgsAK94cxWSxRoiMHAzg9f2EpCURgu9IVc6wI"
        try:
            FUSO_BR = timezone(timedelta(hours=-3))
        except:
            FUSO_BR = None

        HEADERS = {
            "apikey": KEY,
            "Authorization": f"Bearer {KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

        COR_FUNDO = "#F0F4F8"           
        COR_PAINEL = "#FFFFFF"          
        COR_TEXTO = "#102A43"           
        COR_DESTAQUE = "#334E68"        
        COR_BOTAO_PRINCIPAL = "#0B3954" 
        COR_VERDE_SUCESSO = "#27AE60"   
        COR_VERMELHO_ERRO = "#C0392B"   

        # Remove a tela de carregamento para construir o app
        page.controls.clear()

        # HAPTIC FEEDBACK (Vibration)
        hf = ft.HapticFeedback()
        page.overlay.append(hf)

        def mostrar_mensagem(texto, cor):
            page.snack_bar = ft.SnackBar(ft.Text(texto, size=16, color="white"), bgcolor=cor)
            page.snack_bar.open = True
            page.update()

        # =====================================================================
        # MINI-DASHBOARD (Daily Summary)
        # =====================================================================
        def abrir_dashboard():
            def carregar():
                hoje_str = datetime.now(FUSO_BR).strftime('%Y-%m-%d')
                try:
                    resp = requests.get(f"{URL}/rest/v1/vendas?order=id.desc&limit=500&select=*", headers=HEADERS, timeout=5)
                    if resp.ok:
                        vendas = resp.json()
                        vendas_hoje = [v for v in vendas if str(v.get('data_hora', '')).startswith(hoje_str)]
                        total = sum(float(v.get('total_final', v.get('total', 0))) for v in vendas_hoje)
                        qtd = len(vendas_hoje)
                        
                        dlg_dash.content = ft.Column([
                            ft.Text(f"📅 Today: {datetime.now(FUSO_BR).strftime('%m/%d/%Y')}", weight=ft.FontWeight.BOLD),
                            ft.Text(f"Sales made: {qtd}", size=16),
                            ft.Text(f"Revenue: $ {total:.2f}", color=COR_VERDE_SUCESSO, weight=ft.FontWeight.BOLD, size=22)
                        ], tight=True)
                        page.update()
                    else:
                        dlg_dash.content = ft.Text("Error loading data.", color=COR_VERMELHO_ERRO)
                        page.update()
                except Exception:
                    dlg_dash.content = ft.Text("No internet connection.", color=COR_VERMELHO_ERRO)
                    page.update()

            dlg_dash = ft.AlertDialog(
                title=ft.Text("📊 Daily Summary", weight=ft.FontWeight.BOLD),
                content=ft.Container(content=ft.ProgressRing(), padding=20, alignment=ft.alignment.center, width=200, height=100),
                actions=[ft.TextButton("Close", on_click=lambda e: [setattr(dlg_dash, 'open', False), page.update()])]
            )
            page.dialog = dlg_dash
            dlg_dash.open = True
            page.update()
            threading.Thread(target=carregar).start()

        # =====================================================================
        # TOP HEADER WITH BANNER AND DASHBOARD ICON
        # =====================================================================
        icone_dash = ft.IconButton(icon=ft.icons.BAR_CHART, icon_color="white", icon_size=32, tooltip="Today's Summary", on_click=lambda e: abrir_dashboard())
        
        topo_app_content = ft.Row([
            ft.Text("OmniMarket POS", size=24, weight=ft.FontWeight.BOLD, color="white"),
            icone_dash
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        bgcolor_topo = COR_BOTAO_PRINCIPAL
        
        if os.path.exists("assets/banner.png"):
            icone_dash.icon_color = COR_BOTAO_PRINCIPAL
            topo_app_content = ft.Row([
                ft.Image(src="banner.png", fit=ft.ImageFit.CONTAIN, height=60),
                icone_dash
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            bgcolor_topo = COR_FUNDO

        topo_app = ft.Container(
            content=topo_app_content,
            bgcolor=bgcolor_topo, padding=10, width=float('inf')
        )

        # =====================================================================
        # BARCODE SCANNER SYSTEM
        # =====================================================================
        def abrir_leitor_codigo(campo_destino, ao_ler_callback=None):
            input_manual = ft.TextField(
                label="Scanned code or type here", autofocus=True,
                keyboard_type=ft.KeyboardType.NUMBER, border_color=COR_DESTAQUE,
                on_submit=lambda e: confirmar_codigo(e.control.value)
            )

            def confirmar_codigo(valor):
                if valor and str(valor).strip():
                    codigo_final = str(valor).strip()
                    campo_destino.value = codigo_final
                    dialog_camera.open = False
                    page.update()
                    
