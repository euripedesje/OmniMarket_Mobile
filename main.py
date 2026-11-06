import flet as ft
import traceback
import sys
import os

def main(page: ft.Page):
    # =========================================================================
    # 1. IMEDIATAMENTE DESENHAR A INTERFACE (Cura a tela preta)
    # =========================================================================
    page.title = "OmniMarket POS"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#F0F4F8"
    page.padding = 0
    
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

        page.controls.clear()

        hf = ft.HapticFeedback()
        page.overlay.append(hf)

        def mostrar_mensagem(texto, cor):
            page.snack_bar = ft.SnackBar(ft.Text(texto, size=16, color="white"), bgcolor=cor)
            page.snack_bar.open = True
            page.update()

        # =====================================================================
        # MINI-DASHBOARD
        # =====================================================================
        def abrir_dashboard():
            def carregar():
                hoje_str = datetime.now(FUSO_BR).strftime('%Y-%m-%d')
                try:
                    resp = requests.get(f"{URL}/rest/v1/vendas?order=id.desc&limit=1000&select=*", headers=HEADERS, timeout=5)
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

        icone_dash = ft.IconButton(icon=ft.icons.BAR_CHART, icon_color="white", icon_size=32, tooltip="Today's Summary", on_click=lambda e: abrir_dashboard())
        
        topo_app_content = ft.Row([
            ft.Text("OmniMarket POS", size=24, weight=ft.FontWeight.BOLD, color="white"),
            icone_dash
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        bgcolor_topo = COR_BOTAO_PRINCIPAL
        
        if os.path.exists("assets/banner.png"):
            icone_dash.icon_color = COR_BOTAO_PRINCIPAL
            topo_app_content = ft.Row([
                ft.Image(src="assets/banner.png", fit=ft.ImageFit.CONTAIN, height=60),
                icone_dash
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            bgcolor_topo = COR_FUNDO

        topo_app = ft.Container(content=topo_app_content, bgcolor=bgcolor_topo, padding=10, width=float('inf'))

        # =====================================================================
        # BARCODE SCANNER MODAL
        # =====================================================================
        def abrir_leitor_codigo(campo_destino, ao_ler_callback=None):
            input_manual = ft.TextField(label="Scanned code or type here", autofocus=True, keyboard_type=ft.KeyboardType.NUMBER, border_color=COR_DESTAQUE, on_submit=lambda e: confirmar_codigo(e.control.value))
            def confirmar_codigo(valor):
                if valor and str(valor).strip():
                    codigo_final = str(valor).strip()
                    campo_destino.value = codigo_final
                    dialog_camera.open = False
                    page.update()
                    hf.heavy_impact() 
                    mostrar_mensagem(f"Code: {codigo_final}", COR_VERDE_SUCESSO)
                    if ao_ler_callback: ao_ler_callback(codigo_final)
            def colar_da_area_transferencia(e):
                try:
                    texto_colado = page.get_clipboard()
                    if texto_colado and str(texto_colado).strip(): confirmar_codigo(texto_colado)
                    else: mostrar_mensagem("Clipboard is empty!", COR_VERMELHO_ERRO)
                except Exception: mostrar_mensagem("Please paste manually.", COR_DESTAQUE)
            def abrir_camera_externa(e): page.launch_url("https://scanapp.org/")
            
            dialog_camera = ft.AlertDialog(
                modal=True,
                title=ft.Text("📷 Scan Barcode", size=18, weight=ft.FontWeight.BOLD, color=COR_TEXTO),
                content=ft.Container(width=310, content=ft.Column([
                    ft.ElevatedButton("📷 OPEN CAMERA SCANNER", bgcolor=COR_BOTAO_PRINCIPAL, color="white", height=45, width=300, on_click=abrir_camera_externa),
                    ft.ElevatedButton("📋 PASTE SCANNED CODE", bgcolor=COR_DESTAQUE, color="white", height=45, width=300, on_click=colar_da_area_transferencia),
                    ft.Divider(color=COR_DESTAQUE), input_manual,
                ], spacing=10, tight=True)),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda e: [setattr(dialog_camera, 'open', False), page.update()]),
                    ft.ElevatedButton("Confirm", bgcolor=COR_VERDE_SUCESSO, color="white", on_click=lambda e: confirmar_codigo(input_manual.value))
                ], actions_alignment=ft.MainAxisAlignment.END
            )
            page.dialog = dialog_camera
            dialog_camera.open = True
            page.update()

        # =====================================================================
        # EDIT PRODUCT MODAL
        # =====================================================================
        edit_codigo = ft.TextField(label="Barcode", read_only=True, border_color=COR_DESTAQUE)
        edit_nome = ft.TextField(label="Product Name", border_color=COR_DESTAQUE)
        edit_custo = ft.TextField(label="Cost ($)", border_color=COR_DESTAQUE)
        edit_preco = ft.TextField(label="Selling Price ($)", border_color=COR_DESTAQUE)
        edit_estoque = ft.TextField(label="Stock", keyboard_type=ft.KeyboardType.NUMBER, border_color=COR_DESTAQUE)
        
        def salvar_edicao_produto(e):
            try:
                codigo = edit_codigo.value
                n_nome = edit_nome.value.strip()
                n_custo = float(edit_custo.value.replace(',', '.')) if edit_custo.value else 0.0
                n_preco = float(edit_preco.value.replace(',', '.')) if edit_preco.value else 0.0
                n_estoque = int(edit_estoque.value) if edit_estoque.value else 0
                if not n_nome: return mostrar_mensagem("Name cannot be empty.", COR_VERMELHO_ERRO)
                
                dados = {"nome": n_nome, "custo": n_custo, "preco": n_preco, "estoque": n_estoque}
                def processo_salvar():
                    try:
                        cod_url = urllib.parse.quote(codigo)
                        req = requests.patch(f"{URL}/rest/v1/produtos?codigo=eq.{cod_url}", headers=HEADERS, json=dados, timeout=8)
                        if req.ok:
                            mostrar_mensagem("Product updated in cloud!", COR_VERDE_SUCESSO)
                            carregar_estoque(busca_input.value)
                        else: mostrar_mensagem("Error updating in cloud.", COR_VERMELHO_ERRO)
                    except Exception: mostrar_mensagem("Internet failure.", COR_VERMELHO_ERRO)
                
                dialog_edicao.open = False
                page.update()
                threading.Thread(target=processo_salvar).start()
            except ValueError: mostrar_mensagem("Invalid numeric values.", COR_VERMELHO_ERRO)

        dialog_edicao = ft.AlertDialog(
            modal=True, title=ft.Text("✏️ Edit Product", weight=ft.FontWeight.BOLD),
            content=ft.Column([edit_codigo, edit_nome, edit_custo, edit_preco, edit_estoque], tight=True, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: [setattr(dialog_edicao, 'open', False), page.update()]),
                ft.ElevatedButton("Save", bgcolor=COR_VERDE_SUCESSO, color="white", on_click=salvar_edicao_produto)
            ]
        )

        def abrir_edicao_modal(produto):
            edit_codigo.value = produto.get('codigo', '')
            edit_nome.value = produto.get('nome', '')
            edit_custo.value = str(produto.get('custo', 0.0))
            edit_preco.value = str(produto.get('preco', 0.0))
            edit_estoque.value = str(produto.get('estoque', 0))
            page.dialog = dialog_edicao
            dialog_edicao.open = True
            page.update()

        # =====================================================================
        # TAB 1: INVENTORY CHECK
        # =====================================================================
        lista_produtos = ft.ListView(expand=True, spacing=10, padding=10)
        busca_input = ft.TextField(label="🔍 Search name or barcode", expand=True, border_color=COR_DESTAQUE, focused_border_color=COR_BOTAO_PRINCIPAL, on_submit=lambda e: threading.Thread(target=carregar_estoque, args=(e.control.value,)).start())
        dropdown_ordem = ft.Dropdown(options=[ft.dropdown.Option("A-Z"), ft.dropdown.Option("Z-A"), ft.dropdown.Option("Lowest Price"), ft.dropdown.Option("Highest Price"), ft.dropdown.Option("Lowest Stock"), ft.dropdown.Option("Highest Stock")], value="A-Z", height=45, border_color=COR_DESTAQUE, expand=True, on_change=lambda e: threading.Thread(target=carregar_estoque, args=(busca_input.value,)).start())

        def carregar_estoque(termo=""):
            lista_produtos.controls.clear()
            lista_produtos.controls.append(ft.Text("Syncing...", color="gray", text_align=ft.TextAlign.CENTER))
            page.update()
            try:
                ordem_param = "order=nome.asc"
                if dropdown_ordem.value == "Z-A": ordem_param = "order=nome.desc"
                elif dropdown_ordem.value == "Lowest Price": ordem_param = "order=preco.asc"
                elif dropdown_ordem.value == "Highest Price": ordem_param = "order=preco.desc"
                elif dropdown_ordem.value == "Lowest Stock": ordem_param = "order=estoque.asc"
                elif dropdown_ordem.value == "Highest Stock": ordem_param = "order=estoque.desc"

                termo_limpo = str(termo).strip() if termo else ""
                if termo_limpo:
                    if termo_limpo.isdigit(): resp = requests.get(f"{URL}/rest/v1/produtos?codigo=eq.{termo_limpo}&select=*&{ordem_param}&limit=2000", headers=HEADERS, timeout=8)
                    else:
                        termo_url = urllib.parse.quote(termo_limpo)
                        resp = requests.get(f"{URL}/rest/v1/produtos?nome=ilike.*{termo_url}*&select=*&{ordem_param}&limit=2000", headers=HEADERS, timeout=8)
                else: resp = requests.get(f"{URL}/rest/v1/produtos?select=*&{ordem_param}&limit=2000", headers=HEADERS, timeout=8)
                    
                produtos = resp.json()
                lista_produtos.controls.clear()
                
                if not produtos: lista_produtos.controls.append(ft.Text("No products found.", size=16, text_align=ft.TextAlign.CENTER))
                else:
                    for p in produtos:
                        estoque_atual = p.get('estoque', 0)
                        lista_produtos.controls.append(
                            ft.Card(content=ft.Container(padding=15, content=ft.Column([
                                ft.Text(p.get('nome', 'No Name'), weight=ft.FontWeight.BOLD, size=18, color=COR_TEXTO),
                                ft.Row([ft.Text(f"SKU: {p.get('codigo', '')}", color="gray", size=14), ft.Text(f"Stock: {estoque_atual}", color=COR_VERMELHO_ERRO if estoque_atual <= 2 else COR_VERDE_SUCESSO, weight=ft.FontWeight.BOLD, size=14)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Row([ft.Text(f"$ {float(p.get('preco', 0.0)):.2f}", size=20, color=COR_DESTAQUE, weight=ft.FontWeight.BOLD), ft.IconButton(icon=ft.icons.EDIT, icon_color=COR_BOTAO_PRINCIPAL, tooltip="Edit", on_click=lambda e, prod=p: abrir_edicao_modal(prod))], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                            ])), color=COR_PAINEL, elevation=3)
                        )
            except Exception:
                lista_produtos.controls.clear()
                lista_produtos.controls.append(ft.Text("Connection error.", color=COR_VERMELHO_ERRO, text_align=ft.TextAlign.CENTER))
            page.update()

        view_estoque = ft.Column([
            topo_app,
            ft.Container(content=ft.Column([
                ft.Row([busca_input, ft.IconButton(icon=ft.icons.QR_CODE_SCANNER, icon_size=32, icon_color=COR_BOTAO_PRINCIPAL, on_click=lambda e: abrir_leitor_codigo(busca_input, ao_ler_callback=lambda cod: threading.Thread(target=carregar_estoque, args=(cod,)).start())), ft.IconButton(icon=ft.icons.SEARCH, icon_size=32, icon_color=COR_DESTAQUE, on_click=lambda e: threading.Thread(target=carregar_estoque, args=(busca_input.value,)).start())]),
                ft.Row([ft.Text("Sort by:", size=14, weight=ft.FontWeight.BOLD, color=COR_TEXTO), dropdown_ordem])
            ], spacing=5), padding=ft.padding.symmetric(horizontal=10, vertical=5)), lista_produtos
        ], expand=True, spacing=0, visible=True)

        # =====================================================================
        # TAB 2: MOBILE POS (CART)
        # =====================================================================
        carrinho_mobile = []
        produto_atual_venda = {"codigo": "", "nome": "", "preco": 0.0, "custo": 0.0, "estoque": 0}
        
        venda_cod_input = ft.TextField(label="Product Barcode", border_color=COR_DESTAQUE, expand=True, keyboard_type=ft.KeyboardType.NUMBER)
        venda_qtd_input = ft.TextField(label="Qty", value="1", width=60, keyboard_type=ft.KeyboardType.NUMBER, border_color=COR_DESTAQUE, text_align=ft.TextAlign.CENTER)
        
        lbl_venda_nome = ft.Text("No product selected...", size=16, weight=ft.FontWeight.BOLD, color=COR_TEXTO, overflow=ft.TextOverflow.ELLIPSIS, max_lines=1)
        lbl_venda_info = ft.Text("Waiting for scan or search.", size=13, color="gray")
        
        lista_carrinho = ft.ListView(expand=True, spacing=5)
        lbl_total_carrinho = ft.Text("$ 0.00", size=26, weight=ft.FontWeight.BOLD, color=COR_VERDE_SUCESSO)
        combo_pagamento = ft.Dropdown(options=[ft.dropdown.Option("Cash"), ft.dropdown.Option("Apple/Google Pay"), ft.dropdown.Option("Credit Card"), ft.dropdown.Option("Debit Card"), ft.dropdown.Option("Store Credit")], value="Cash", border_color=COR_DESTAQUE, expand=True, height=50)

        def atualizar_ui_carrinho():
            lista_carrinho.controls.clear()
            total_venda = 0.0
            if not carrinho_mobile: lista_carrinho.controls.append(ft.Text("Cart is empty.", color="gray", text_align=ft.TextAlign.CENTER))
            else:
                for idx, item in enumerate(carrinho_mobile):
                    total_venda += item['subtotal']
                    lista_carrinho.controls.append(
                        ft.Card(elevation=1, color=COR_PAINEL, content=ft.ListTile(title=ft.Text(f"{item['qtd']}x {item['nome']}", weight=ft.FontWeight.BOLD, size=14), subtitle=ft.Text(f"$ {item['preco']:.2f} ea | Sub: $ {item['subtotal']:.2f}", size=13), trailing=ft.IconButton(icon=ft.icons.DELETE, icon_color=COR_VERMELHO_ERRO, on_click=lambda e, i=idx: remover_do_carrinho(i))))
                    )
            lbl_total_carrinho.value = f"$ {total_venda:.2f}"
            page.update()

        def remover_do_carrinho(index):
            if 0 <= index < len(carrinho_mobile):
                removido = carrinho_mobile.pop(index)
                mostrar_mensagem(f"Removed: {removido['nome']}", COR_DESTAQUE)
                atualizar_ui_carrinho()

        def cancelar_venda(e=None):
            carrinho_mobile.clear()
            produto_atual_venda["codigo"] = ""; venda_cod_input.value = ""; venda_qtd_input.value = "1"
            lbl_venda_nome.value = "No product selected..."; lbl_venda_info.value = "Waiting for scan or search."
            combo_pagamento.value = "Cash"
            atualizar_ui_carrinho()
            mostrar_mensagem("Sale cancelled.", COR_VERMELHO_ERRO)

        def processar_leitura_venda(codigo):
            cod_limpo = str(codigo).strip()
            if not cod_limpo: return
            lbl_venda_nome.value = "Searching..."
            lbl_venda_info.value = ""
            page.update()
            
            def buscar():
                try:
                    cod_url = urllib.parse.quote(cod_limpo)
                    resp = requests.get(f"{URL}/rest/v1/produtos?codigo=eq.{cod_url}&select=*", headers=HEADERS, timeout=5)
                    produtos = resp.json()
                    if produtos and len(produtos) > 0:
                        p = produtos[0]
                        produto_atual_venda["codigo"] = p.get('codigo', '')
                        produto_atual_venda["nome"] = p.get('nome', '')
                        produto_atual_venda["preco"] = float(p.get('preco', 0.0))
                        produto_atual_venda["custo"] = float(p.get('custo', 0.0))
                        produto_atual_venda["estoque"] = int(p.get('estoque', 0))
                        lbl_venda_nome.value = produto_atual_venda["nome"]
                        lbl_venda_info.value = f"$ {produto_atual_venda['preco']:.2f} | Stock: {produto_atual_venda['estoque']}"
                        hf.heavy_impact() 
                        mostrar_mensagem("Item ready to add!", COR_BOTAO_PRINCIPAL)
                    else:
                        lbl_venda_nome.value = "Not registered!"
                        lbl_venda_info.value = "Check barcode."
                        produto_atual_venda["codigo"] = ""
                    page.update()
                except Exception:
                    lbl_venda_nome.value = "Network Error"
                    page.update()
            threading.Thread(target=buscar).start()

        venda_cod_input.on_submit = lambda e: processar_leitura_venda(e.control.value)

        def adicionar_ao_carrinho(e):
            if not produto_atual_venda["codigo"]: return mostrar_mensagem("Scan or search an item first!", COR_VERMELHO_ERRO)
            try:
                qtd = int(venda_qtd_input.value)
                if qtd <= 0: raise ValueError
            except: return mostrar_mensagem("Invalid quantity!", COR_VERMELHO_ERRO)
            
            qtd_ja_no_carrinho = sum(i['qtd'] for i in carrinho_mobile if i['codigo'] == produto_atual_venda["codigo"])
            if (qtd + qtd_ja_no_carrinho) > produto_atual_venda["estoque"]:
                return mostrar_mensagem(f"Insufficient stock! (Avail: {produto_atual_venda['estoque']})", COR_VERMELHO_ERRO)
                
            subtotal = produto_atual_venda["preco"] * qtd
            item_existente = next((i for i in carrinho_mobile if i['codigo'] == produto_atual_venda["codigo"]), None)
            
            if item_existente:
                item_existente['qtd'] += qtd
                item_existente['subtotal'] += subtotal
            else:
                carrinho_mobile.append({"codigo": produto_atual_venda["codigo"], "nome": produto_atual_venda["nome"], "preco": produto_atual_venda["preco"], "custo": produto_atual_venda["custo"], "estoque": produto_atual_venda["estoque"], "qtd": qtd, "subtotal": subtotal})
                
            produto_atual_venda["codigo"] = ""; venda_cod_input.value = ""; venda_qtd_input.value = "1"
            lbl_venda_nome.value = "Added!"; lbl_venda_info.value = "Scan the next item."
            hf.heavy_impact() 
            atualizar_ui_carrinho()
            mostrar_mensagem("Added to cart!", COR_VERDE_SUCESSO)

        # AVULSO MODAL
        avulso_desc_input = ft.TextField(label="Description", value="Custom Item", border_color=COR_DESTAQUE)
        avulso_preco_input = ft.TextField(label="Item Price ($)", keyboard_type=ft.KeyboardType.NUMBER, border_color=COR_DESTAQUE)
        avulso_qtd_input = ft.TextField(label="Quantity", value="1", keyboard_type=ft.KeyboardType.NUMBER, border_color=COR_DESTAQUE)
        
        def confirmar_avulso(e):
            try:
                preco = float(avulso_preco_input.value.replace(",", "."))
                qtd = int(avulso_qtd_input.value)
                desc = avulso_desc_input.value.strip() if avulso_desc_input.value.strip() else "Custom Item"
                if preco <= 0 or qtd <= 0: raise ValueError
                carrinho_mobile.append({"codigo": "AVULSO", "nome": desc, "preco": preco, "custo": 0.0, "estoque": 999, "qtd": qtd, "subtotal": preco * qtd})
                dialog_avulso.open = False
                page.update()
                hf.heavy_impact() 
                atualizar_ui_carrinho()
                mostrar_mensagem("Custom Item Added!", COR_VERDE_SUCESSO)
            except ValueError: mostrar_mensagem("Invalid values!", COR_VERMELHO_ERRO)

        dialog_avulso = ft.AlertDialog(
            modal=True, title=ft.Text("🛒 Custom Item", weight=ft.FontWeight.BOLD),
            content=ft.Column([avulso_desc_input, avulso_preco_input, avulso_qtd_input], tight=True),
            actions=[ft.TextButton("Cancel", on_click=lambda e: [setattr(dialog_avulso, 'open', False), page.update()]), ft.ElevatedButton("Add to Cart", bgcolor=COR_VERDE_SUCESSO, color="white", on_click=confirmar_avulso)]
        )
        def abrir_dialog_avulso(e):
            avulso_desc_input.value = "Custom Item"; avulso_preco_input.value = ""; avulso_qtd_input.value = "1"
            page.dialog = dialog_avulso
            dialog_avulso.open = True
            page.update()

        # BUSCA MODAL
        produtos_em_memoria = []
        lista_busca_resultados = ft.ListView(height=300, spacing=5)
        def executar_busca_nome_local(e):
            termo = busca_nome_input.value.strip().lower()
            lista_busca_resultados.controls.clear()
            for p in produtos_em_memoria:
                if not termo or termo in str(p.get('nome', '')).lower() or termo in str(p.get('codigo', '')):
                    def selecionar(e, cod=p.get('codigo')):
                        dialog_busca.open = False
                        venda_cod_input.value = cod
                        page.update()
                        processar_leitura_venda(cod)
                    lista_busca_resultados.controls.append(ft.ListTile(title=ft.Text(p.get('nome', ''), weight=ft.FontWeight.BOLD), subtitle=ft.Text(f"$ {p.get('preco', 0):.2f} | Stock: {p.get('estoque', 0)}"), on_click=selecionar))
            page.update()

        busca_nome_input = ft.TextField(label="Type name here...", border_color=COR_DESTAQUE, on_change=executar_busca_nome_local)
        def carregar_dados_busca():
            nonlocal produtos_em_memoria
            try:
                resp = requests.get(f"{URL}/rest/v1/produtos?order=nome.asc&select=*&limit=1000", headers=HEADERS, timeout=8)
                if resp.ok:
                    produtos_em_memoria = resp.json()
                    executar_busca_nome_local(None)
                else:
                    lista_busca_resultados.controls.clear(); lista_busca_resultados.controls.append(ft.Text("Failed to load.", color=COR_VERMELHO_ERRO)); page.update()
            except Exception:
                lista_busca_resultados.controls.clear(); lista_busca_resultados.controls.append(ft.Text("Connection error.", color=COR_VERMELHO_ERRO)); page.update()

        dialog_busca = ft.AlertDialog(
            modal=True, title=ft.Text("🔍 Search by Name", weight=ft.FontWeight.BOLD),
            content=ft.Container(width=320, content=ft.Column([ft.Container(content=busca_nome_input, padding=ft.padding.only(bottom=10)), lista_busca_resultados], tight=True)),
            actions=[ft.TextButton("Close", on_click=lambda e: [setattr(dialog_busca, 'open', False), page.update()])]
        )
        def abrir_dialog_busca(e):
            busca_nome_input.value = ""; lista_busca_resultados.controls.clear(); lista_busca_resultados.controls.append(ft.Text("Loading all products...", color="gray"))
            page.dialog = dialog_busca
            dialog_busca.open = True
            page.update()
            threading.Thread(target=carregar_dados_busca).start()

        # CHECKOUT
        def perguntar_whatsapp(total, pagamento, itens_copia):
            msg_itens = ""
            for i in itens_copia: msg_itens += f"• {i['qtd']}x {i['nome']} ($ {i['preco']:.2f}) = $ {i['subtotal']:.2f}\n"
            texto_zap = f"*OMNIMARKET POS*\n_Sales Receipt_\n\n*Items:*\n{msg_itens}\n*Total:* $ {total:.2f}\n*Tender:* {pagamento}\n\nThank you for your business!"
            texto_zap_encoded = urllib.parse.quote(texto_zap)
            link_zap = f"https://wa.me/?text={texto_zap_encoded}"

            dlg_zap = ft.AlertDialog(
                modal=True, title=ft.Text("📱 Send Receipt?"), content=ft.Text("Checkout complete!\nDo you want to send the receipt via WhatsApp?"),
                actions=[
                    ft.TextButton("No", on_click=lambda e: [setattr(dlg_zap, 'open', False), page.update()]),
                    ft.ElevatedButton("Yes", bgcolor=COR_VERDE_SUCESSO, color="white", icon=ft.icons.SEND, on_click=lambda e: [page.launch_url(link_zap), setattr(dlg_zap, 'open', False), page.update()])
                ]
            )
            page.dialog = dlg_zap
            dlg_zap.open = True
            page.update()

        def finalizar_venda(e):
            if not carrinho_mobile: return mostrar_mensagem("Cart is empty!", COR_VERMELHO_ERRO)
            total_venda = sum(i['subtotal'] for i in carrinho_mobile)
            forma_pagamento = combo_pagamento.value
            carrinho_mobile_copia = carrinho_mobile.copy() 
            data_atual = datetime.now(FUSO_BR).strftime("%Y-%m-%d %H:%M:%S")
            dados_venda = {"data_hora": data_atual, "subtotal": total_venda, "desconto": 0.0, "total": total_venda, "total_final": total_venda, "forma_pagamento": forma_pagamento}
            
            def enviar_nuvem():
                try:
                    venda_id = None
                    req_venda = requests.post(f"{URL}/rest/v1/vendas", headers=HEADERS, json=dados_venda, timeout=8)
                    if not req_venda.ok:
                        dados_venda_fallback = {"data_hora": data_atual, "total": total_venda, "forma_pagamento": forma_pagamento}
                        req_venda = requests.post(f"{URL}/rest/v1/vendas", headers=HEADERS, json=dados_venda_fallback, timeout=8)
                    if req_venda.ok:
                        res_venda = req_venda.json()
                        venda_id = res_venda[0].get("id") if isinstance(res_venda, list) and len(res_venda) > 0 else None
                    if venda_id:
                        alertas_estoque = []
                        try:
                            req_map = requests.get(f"{URL}/rest/v1/itens_venda?select=*&limit=1", headers=HEADERS, timeout=5)
                            colunas_existentes = list(req_map.json()[0].keys()) if req_map.ok and isinstance(req_map.json(), list) and len(req_map.json()) > 0 else []
                        except: colunas_existentes = []
                        
                        for item in carrinho_mobile:
                            dados_item = {"venda_id": venda_id}
                            if colunas_existentes:
                                if "codigo_barras" in colunas_existentes: dados_item["codigo_barras"] = str(item['codigo'])
                                elif "codigo" in colunas_existentes: dados_item["codigo"] = str(item['codigo'])
                                if "nome_produto" in colunas_existentes: dados_item["nome_produto"] = str(item['nome'])
                                elif "produto" in colunas_existentes: dados_item["produto"] = str(item['nome'])
                                if "qtd" in colunas_existentes: dados_item["qtd"] = int(item['qtd'])
                                elif "quantidade" in colunas_existentes: dados_item["quantidade"] = int(item['qtd'])
                                if "preco_unit" in colunas_existentes: dados_item["preco_unit"] = float(item['preco'])
                                elif "preco" in colunas_existentes: dados_item["preco"] = float(item['preco'])
                                if "subtotal" in colunas_existentes: dados_item["subtotal"] = float(item['subtotal'])
                                elif "total" in colunas_existentes: dados_item["total"] = float(item['subtotal'])
                            else: dados_item = {"venda_id": venda_id, "produto": item['nome'], "quantidade": item['qtd'], "preco": item['preco']}
                            requests.post(f"{URL}/rest/v1/itens_venda", headers=HEADERS, json=dados_item, timeout=8)
                            
                            if item["codigo"] != "AVULSO":
                                novo_estoque = item["estoque"] - item["qtd"]
                                cod_url = urllib.parse.quote(item["codigo"])
                                req_patch = requests.patch(f"{URL}/rest/v1/produtos?codigo=eq.{cod_url}", headers=HEADERS, json={"estoque": novo_estoque}, timeout=5)
                                if req_patch.ok and novo_estoque <= 2:
                                    alertas_estoque.append(item["nome"])
                                    requests.post(f"{URL}/rest/v1/lista_compras", headers=HEADERS, json={"produto": item["nome"], "observacao": f"Low stock (Remaining {novo_estoque})"}, timeout=5)
                        
                        mostrar_mensagem(f"Checkout Complete! ($ {total_venda:.2f})", COR_VERDE_SUCESSO)
                        if alertas_estoque: mostrar_mensagem(f"⚠️ {len(alertas_estoque)} items are low on stock.", COR_DESTAQUE)
                        
                        carrinho_mobile.clear()
                        produto_atual_venda["codigo"] = ""; venda_cod_input.value = ""; venda_qtd_input.value = "1"
                        lbl_venda_nome.value = "No product selected..."; lbl_venda_info.value = "Waiting for scan or search."
                        combo_pagamento.value = "Cash"
                        page.update()
                        atualizar_ui_carrinho()
                        perguntar_whatsapp(total_venda, forma_pagamento, carrinho_mobile_copia)
                    else: mostrar_mensagem("Failed to create sale ID.", COR_VERMELHO_ERRO)
                except Exception as e: mostrar_mensagem("Network error during checkout.", COR_VERMELHO_ERRO)
            
            mostrar_mensagem("Processing checkout...", COR_BOTAO_PRINCIPAL)
            threading.Thread(target=enviar_nuvem).start()

        view_vender = ft.Column([
            ft.Container(content=ft.Text("Point of Sale (POS)", size=22, weight=ft.FontWeight.BOLD, color="white"), bgcolor=COR_VERDE_SUCESSO, padding=12, alignment=ft.alignment.center),
            ft.Container(content=ft.Column([
                ft.Row([venda_cod_input, ft.IconButton(icon=ft.icons.QR_CODE_SCANNER, icon_size=35, icon_color=COR_BOTAO_PRINCIPAL, on_click=lambda e: abrir_leitor_codigo(venda_cod_input, ao_ler_callback=processar_leitura_venda)), ft.IconButton(icon=ft.icons.SEARCH, icon_size=35, icon_color=COR_DESTAQUE, on_click=abrir_dialog_busca)]),
                ft.Row([venda_qtd_input, ft.Container(content=ft.Column([lbl_venda_nome, lbl_venda_info], spacing=2), expand=True), ft.IconButton(icon=ft.icons.ADD_CIRCLE, icon_size=45, icon_color=COR_VERDE_SUCESSO, on_click=adicionar_ao_carrinho)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.ElevatedButton("🛒 ADD CUSTOM ITEM", width=float('inf'), height=40, bgcolor=COR_BOTAO_PRINCIPAL, color="white", on_click=abrir_dialog_avulso),
                ft.Divider(color=COR_DESTAQUE), ft.Text("🛒 Shopping Cart:", weight=ft.FontWeight.BOLD),
                ft.Container(content=lista_carrinho, expand=True, border=ft.border.all(1, COR_DESTAQUE), border_radius=8, padding=5, bgcolor="#FDF8F0"),
                ft.Divider(color=COR_DESTAQUE), ft.Row([ft.Text("Total:", size=22, weight=ft.FontWeight.BOLD, color=COR_TEXTO), lbl_total_carrinho], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([ft.Text("Tender:", weight=ft.FontWeight.BOLD), combo_pagamento]),
                ft.Row([ft.ElevatedButton("CANCEL", expand=True, height=50, bgcolor=COR_VERMELHO_ERRO, color="white", on_click=cancelar_venda), ft.ElevatedButton("CHECKOUT", expand=True, height=50, bgcolor=COR_VERDE_SUCESSO, color="white", on_click=finalizar_venda)], spacing=10)
            ], spacing=10, expand=True), padding=15, expand=True)
        ], expand=True, spacing=0, visible=False)
        atualizar_ui_carrinho()

        # =====================================================================
        # TAB 3: REGISTER PRODUCT
        # =====================================================================
        aviso_conflito_txt = ft.Text("", color=COR_VERMELHO_ERRO, size=13, weight=ft.FontWeight.BOLD, visible=False)
        def verificar_codigo_existente(codigo_verificar):
            if not codigo_verificar or not str(codigo_verificar).strip():
                aviso_conflito_txt.visible = False
                page.update()
                return
            def checar():
                try:
                    cod_limpo = urllib.parse.quote(str(codigo_verificar).strip())
                    resp = requests.get(f"{URL}/rest/v1/produtos?codigo=eq.{cod_limpo}&select=*", headers=HEADERS, timeout=5)
                    existentes = resp.json()
                    if existentes and isinstance(existentes, list) and len(existentes) > 0:
                        prod_antigo = existentes[0]
                        aviso_conflito_txt.value = f"⚠️ Barcode already used by: '{prod_antigo.get('nome')}' (Stock: {prod_antigo.get('estoque')})"
                        aviso_conflito_txt.visible = True
                    else: aviso_conflito_txt.visible = False
                    page.update()
                except Exception: pass
            threading.Thread(target=checar).start()

        cad_codigo = ft.TextField(label="Barcode", keyboard_type=ft.KeyboardType.NUMBER, border_color=COR_DESTAQUE, on_blur=lambda e: verificar_codigo_existente(e.control.value), on_submit=lambda e: verificar_codigo_existente(e.control.value))
        cad_nome = ft.TextField(label="Product Name", border_color=COR_DESTAQUE)
        cad_custo = ft.TextField(label="Cost ($)", border_color=COR_DESTAQUE)
        cad_preco = ft.TextField(label="Selling Price ($)", border_color=COR_DESTAQUE)
        cad_estoque = ft.TextField(label="Quantity in Stock", keyboard_type=ft.KeyboardType.NUMBER, border_color=COR_DESTAQUE)

        def limpar_campos_cadastro():
            cad_codigo.value = ""; cad_nome.value = ""; cad_custo.value = ""; cad_preco.value = ""; cad_estoque.value = ""
            aviso_conflito_txt.visible = False; page.update()

        def gravar_no_banco_direto(dados, modo="inserir"):
            try:
                if modo == "inserir": requests.post(f"{URL}/rest/v1/produtos", headers=HEADERS, json=dados, timeout=8)
                elif modo == "atualizar":
                    cod_url = urllib.parse.quote(str(dados["codigo"]))
                    requests.patch(f"{URL}/rest/v1/produtos?codigo=eq.{cod_url}", headers=HEADERS, json=dados, timeout=8)
                limpar_campos_cadastro()
                mostrar_mensagem(f"'{dados['nome']}' saved successfully!", COR_VERDE_SUCESSO)
            except Exception: mostrar_mensagem("Network error while saving!", COR_VERMELHO_ERRO)

        def abrir_modal_conflito(prod_existente, dados_novos):
            nome_antigo = prod_existente.get("nome", "No Name"); estoque_antigo = int(prod_existente.get("estoque", 0)); preco_antigo = float(prod_existente.get("preco", 0.0))
            def acao_gerar_novo_codigo(e):
                dialog_conflito.open = False
                novo_cod_exclusivo = str(random.randint(10000000, 99999999)); dados_novos["codigo"] = novo_cod_exclusivo
                mostrar_mensagem(f"Saving with new barcode ({novo_cod_exclusivo})...", COR_DESTAQUE)
                threading.Thread(target=gravar_no_banco_direto, args=(dados_novos, "inserir")).start()
            def acao_somar_estoque(e):
                dialog_conflito.open = False
                dados_novos["estoque"] = estoque_antigo + dados_novos["estoque"]
                mostrar_mensagem("Adding stock and updating...", COR_DESTAQUE)
                threading.Thread(target=gravar_no_banco_direto, args=(dados_novos, "atualizar")).start()
            def acao_substituir_tudo(e):
                dialog_conflito.open = False
                mostrar_mensagem("Overwrite previous product...", COR_DESTAQUE)
                threading.Thread(target=gravar_no_banco_direto, args=(dados_novos, "atualizar")).start()

            dialog_conflito = ft.AlertDialog(
                modal=True, title=ft.Text("⚠️ Duplicate Barcode!", size=18, weight=ft.FontWeight.BOLD, color=COR_VERMELHO_ERRO),
                content=ft.Container(width=310, content=ft.Column([
                    ft.Text(f"The barcode {dados_novos['codigo']} is already in the system:", size=14),
                    ft.Container(padding=10, bgcolor="#FFF3CD", border_radius=8, content=ft.Column([ft.Text(f"📦 Current: {nome_antigo}", weight=ft.FontWeight.BOLD, color=COR_TEXTO), ft.Text(f"💰 Price: $ {preco_antigo:.2f} | Stock: {estoque_antigo}", size=13, color="#856404")], spacing=4)),
                    ft.Text(f"You are trying to save: '{dados_novos['nome']}'", size=14, weight=ft.FontWeight.BOLD), ft.Divider(), ft.Text("What do you want to do?", size=14, color="gray"),
                    ft.ElevatedButton("🎲 Generate New Barcode", bgcolor=COR_VERDE_SUCESSO, color="white", width=300, on_click=acao_gerar_novo_codigo),
                    ft.ElevatedButton(f"➕ Add Stock", bgcolor=COR_DESTAQUE, color="white", width=300, on_click=acao_somar_estoque),
                    ft.ElevatedButton("🔄 Overwrite Old Product", bgcolor=COR_VERMELHO_ERRO, color="white", width=300, on_click=acao_substituir_tudo),
                ], spacing=10, tight=True)), actions=[ft.TextButton("Cancel", on_click=lambda e: [setattr(dialog_conflito, 'open', False), page.update()])]
            )
            page.dialog = dialog_conflito
            dialog_conflito.open = True
            page.update()

        def salvar_produto(e):
            codigo = cad_codigo.value.strip() if cad_codigo.value else ""
            nome = cad_nome.value.strip() if cad_nome.value else ""
            if not codigo or not nome: return mostrar_mensagem("Barcode and Name are required!", COR_VERMELHO_ERRO)
            try:
                custo = float(cad_custo.value.replace(',', '.')) if cad_custo.value else 0.0
                preco_digitado = float(cad_preco.value.replace(',', '.')) if cad_preco.value else 0.0
                if preco_digitado == 0.0 and custo > 0:
                    preco_base = custo * 2.0; centavos = int(round(preco_base * 100)); ultimo_digito = centavos % 10
                    preco_final = (centavos + (9 - ultimo_digito)) / 100.0 if ultimo_digito < 9 else preco_base
                else: preco_final = preco_digitado
                estoque = int(cad_estoque.value) if cad_estoque.value else 0
                dados = {"codigo": codigo, "nome": nome, "custo": custo, "preco": preco_final, "estoque": estoque}
                def processo_verificar_e_salvar():
                    try:
                        cod_url = urllib.parse.quote(codigo)
                        resp = requests.get(f"{URL}/rest/v1/produtos?codigo=eq.{cod_url}&select=*", headers=HEADERS, timeout=8)
                        existentes = resp.json()
                        if existentes and isinstance(existentes, list) and len(existentes) > 0: abrir_modal_conflito(existentes[0], dados)
                        else: gravar_no_banco_direto(dados, "inserir")
                    except Exception: mostrar_mensagem("Network error while checking database!", COR_VERMELHO_ERRO)
                mostrar_mensagem("Verifying barcode in cloud...", COR_DESTAQUE)
                threading.Thread(target=processo_verificar_e_salvar).start()
            except Exception: mostrar_mensagem("Value error! Use numbers only.", COR_VERMELHO_ERRO)

        view_cadastrar = ft.Column([
            ft.Container(content=ft.Text("Quick Register", size=24, weight=ft.FontWeight.BOLD, color="white"), bgcolor=COR_DESTAQUE, padding=15, alignment=ft.alignment.center),
            ft.Container(content=ft.Column([
                ft.Row([ft.Container(content=cad_codigo, expand=True), ft.IconButton(icon=ft.icons.QR_CODE_SCANNER, icon_size=35, icon_color=COR_BOTAO_PRINCIPAL, on_click=lambda e: abrir_leitor_codigo(cad_codigo, ao_ler_callback=verificar_codigo_existente)), ft.IconButton(icon=ft.icons.CASINO, icon_size=35, icon_color=COR_DESTAQUE, on_click=lambda e: [setattr(cad_codigo, 'value', str(random.randint(10000000, 99999999))), page.update()])]),
                aviso_conflito_txt, cad_nome, cad_custo, cad_preco, cad_estoque,
                ft.ElevatedButton("💾 SAVE PRODUCT", height=50, bgcolor=COR_VERDE_SUCESSO, color="white", on_click=salvar_produto, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))
            ], spacing=15, scroll=ft.ScrollMode.AUTO), padding=20, expand=True)
        ], expand=True, spacing=0, visible=False)

        # =====================================================================
        # TAB 4: RESTOCK LIST
        # =====================================================================
        compra_nome = ft.TextField(label="What is missing in store?", border_color=COR_DESTAQUE)
        compra_obs = ft.TextField(label="Notes / Qty (Optional)", border_color=COR_DESTAQUE)
        lista_compras_view = ft.ListView(expand=True, spacing=10)

        def carregar_compras():
            def processo_compras():
                try:
                    resp = requests.get(f"{URL}/rest/v1/lista_compras?select=*&order=id.desc", headers=HEADERS, timeout=8)
                    lista_compras_view.controls.clear()
                    itens = resp.json()
                    if not itens: lista_compras_view.controls.append(ft.Text("Restock list is empty.", color="gray", text_align=ft.TextAlign.CENTER))
                    else:
                        for c in itens:
                            lista_compras_view.controls.append(ft.Card(color=COR_PAINEL, elevation=2, content=ft.ListTile(leading=ft.Icon(ft.icons.SHOPPING_BAG, color=COR_DESTAQUE), title=ft.Text(c.get('produto', ''), weight=ft.FontWeight.BOLD, color=COR_TEXTO), subtitle=ft.Text(c.get('observacao', '') or "No notes"), trailing=ft.IconButton(ft.icons.DELETE_OUTLINE, icon_color=COR_VERMELHO_ERRO, data=c.get('id'), on_click=deletar_compra))))
                    page.update()
                except Exception: pass
            threading.Thread(target=processo_compras).start()

        def adicionar_compra(e):
            if not compra_nome.value or not compra_nome.value.strip(): return mostrar_mensagem("Enter the missing product name!", COR_VERMELHO_ERRO)
            dados = {"produto": compra_nome.value.strip(), "observacao": compra_obs.value.strip() if compra_obs.value else ""}
            compra_nome.value = ""; compra_obs.value = ""; page.update()
            def processo_add():
                try:
                    requests.post(f"{URL}/rest/v1/lista_compras", headers=HEADERS, json=dados, timeout=8)
                    mostrar_mensagem("Added to restock list!", COR_VERDE_SUCESSO); carregar_compras()
                except Exception: mostrar_mensagem("Error adding item.", COR_VERMELHO_ERRO)
            threading.Thread(target=processo_add).start()

        def deletar_compra(e):
            item_id = e.control.data
            def processo_del():
                try:
                    requests.delete(f"{URL}/rest/v1/lista_compras?id=eq.{item_id}", headers=HEADERS, timeout=8)
                    mostrar_mensagem("Item removed from list!", COR_VERDE_SUCESSO); carregar_compras()
                except Exception: pass
            threading.Thread(target=processo_del).start()

        view_compras = ft.Column([
            ft.Container(content=ft.Text("Restock List", size=24, weight=ft.FontWeight.BOLD, color="white"), bgcolor=COR_BOTAO_PRINCIPAL, padding=15, alignment=ft.alignment.center),
            ft.Container(content=ft.Column([compra_nome, compra_obs, ft.ElevatedButton("➕ ADD TO LIST", height=45, bgcolor=COR_DESTAQUE, color="white", on_click=adicionar_compra, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))), ft.Divider(color=COR_DESTAQUE), lista_compras_view], spacing=10, expand=True), padding=20, expand=True)
        ], expand=True, spacing=0, visible=False)

        # =====================================================================
        # BOTTOM NAVIGATION BAR
        # =====================================================================
        def mudar_aba(e):
            idx = e.control.selected_index
            view_estoque.visible = (idx == 0); view_vender.visible = (idx == 1); view_cadastrar.visible = (idx == 2); view_compras.visible = (idx == 3)
            if idx == 0: threading.Thread(target=carregar_estoque).start()
            elif idx == 3: carregar_compras()
            page.update()

        page.navigation_bar = ft.NavigationBar(
            selected_index=0, bgcolor=COR_PAINEL, indicator_color=COR_FUNDO, on_change=mudar_aba,
            destinations=[
                ft.NavigationDestination(icon=ft.icons.INVENTORY_2_OUTLINED, selected_icon=ft.icons.INVENTORY_2, label="Inventory"),
                ft.NavigationDestination(icon=ft.icons.POINT_OF_SALE_OUTLINED, selected_icon=ft.icons.POINT_OF_SALE, label="POS"),
                ft.NavigationDestination(icon=ft.icons.ADD_BOX_OUTLINED, selected_icon=ft.icons.ADD_BOX, label="Register"),
                ft.NavigationDestination(icon=ft.icons.SHOPPING_CART_OUTLINED, selected_icon=ft.icons.SHOPPING_CART, label="Restock"),
            ]
        )

        page.add(view_estoque, view_vender, view_cadastrar, view_compras)
        threading.Thread(target=carregar_estoque).start()
        
    except Exception:
        page.controls.clear()
        page.add(ft.Container(padding=20, content=ft.Column([ft.Text("🚨 CRITICAL APP ERROR", color="red", weight=ft.FontWeight.BOLD, size=20), ft.Text(str(traceback.format_exc()), color="black", size=12)], scroll=ft.ScrollMode.AUTO)))
        page.update()

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
