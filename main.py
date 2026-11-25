from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time, csv, os

# Configura as opções do Chrome
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)

# Inicializa o navegador com as opções
driver = webdriver.Chrome(options=chrome_options)

# Faz login no GSAN
username = ""
password = ""
login_url = "https://g1.caema.ma.gov.br/gsan/"
manter_conta = "https://g1.caema.ma.gov.br/gsan/exibirManterContaAction.do?menu=sim"
driver.get(login_url)

driver.find_element(By.XPATH, "//input[@name='login']").send_keys(username)
driver.find_element(By.XPATH, "//input[@name='senha']").send_keys(password)
driver.find_element(By.XPATH, "//input[@name='buttonLogin']").click()

time.sleep(0.5)
driver.get(manter_conta)

meses = {
    "jan": 1, "fev": 2, "mar": 3, "abr": 4,
    "mai": 5, "jun": 6, "jul": 7, "ago": 8,
    "set": 9, "out": 10, "nov": 11, "dez": 12,
}

# Ajuste o nome do arquivo de entrada conforme necessário
arquivo_csv = './milMatriculasParaRetificar.csv'
arquivo_erros_historico = './ErroHistoricoRetificados.csv'

# Conjunto para armazenar (matricula, referencia) já processados anteriormente
ja_processadas = set()

# 1. Cria o CSV de histórico/erros se não existir, ou lê os registros já feitos
if not os.path.exists(arquivo_erros_historico):
    with open(arquivo_erros_historico, 'w', newline='', encoding='utf-8') as f_erro:
        writer_erro = csv.writer(f_erro, delimiter=',')
        writer_erro.writerow(["Matricula", "Referencia", "Valor", "Status"])
else:
    with open(arquivo_erros_historico, 'r', encoding='utf-8') as f_erro:
        reader_erro = csv.reader(f_erro, delimiter=',')
        next(reader_erro, None)  # Pula o cabeçalho
        for linha in reader_erro:
            if len(linha) >= 2:
                ja_processadas.add((linha[0].strip(), linha[1].strip()))

print(f"Total de registros já processados encontrados no histórico: {len(ja_processadas)}")

# Função auxiliar para registrar o status no CSV imediatamente
def registrar_status(matricula, referencia, valor, status):
    with open(arquivo_erros_historico, 'a', newline='', encoding='utf-8') as f_erro:
        writer_erro = csv.writer(f_erro, delimiter=',')
        writer_erro.writerow([matricula, referencia, valor, status])
    ja_processadas.add((matricula, referencia))

# ==============================================================================
# LOOP AUTOMÁTICO PELAS LINHAS DO CSV
# ==============================================================================
with open(arquivo_csv, 'r', encoding='utf-8') as archive:
    reader = csv.reader(archive, delimiter=',')
    next(reader, None)  # Pula o cabeçalho

    for collun in reader:
        if len(collun) < 3 or not collun[0].strip():
            continue

        matricula = collun[0].strip()
        referencia = collun[1].strip()
        valor_bruto = collun[2].strip()

        # Verifica se esta Matrícula + Referência já foi processada antes (sucesso ou erro)
        if (matricula, referencia) in ja_processadas:
            print(f"Pulando Matrícula: {matricula} | Ref: {referencia} (já registrada anteriormente).")
            continue

        print(f"Processando Matrícula: {matricula} | Ref: {referencia}")

        # 1. Pesquisa a matrícula
        matricula_field = driver.find_element(By. XPATH, value="//input[@name='idImovel']")
        time.sleep(0.9)
        matricula_field.clear()
        time.sleep(0.7)
        matricula_field.send_keys(matricula, Keys.RETURN)

        # 2. Prepara o texto da data (mm/aaaa)
        mes_abreviado, ano = referencia.split("/", 1)
        mes_numero = meses[mes_abreviado.strip().lower().rstrip(".")]
        ano_limpo = ano.strip()
        if len(ano_limpo) == 2:
            ano_limpo = f"20{ano_limpo}"

        texto_link = f"{mes_numero:02d}/{ano_limpo}"
        xpathA = f"//a[normalize-space(.)='{texto_link}']"

        # 3. Tenta encontrar e clicar na referência da conta
        try:
            botton_idImovel = driver.find_element(By.XPATH, value = xpathA)
            time.sleep(0.7)
            botton_idImovel.click()

        except (TimeoutException, NoSuchElementException):
            print(f"-> Erro na Matrícula {matricula} ({texto_link}): Referencia Não Clickavel")
            registrar_status(matricula, referencia, valor_bruto, "Referencia Não Clickavel")
            continue

        # 3.1. Verifica se apareceu a tela de aviso com os botões Confirmar e Voltar (Conta Paga)
        conta_estava_paga = False
        time.sleep(0.5)

        botoes_confirmar = driver.find_elements(By.XPATH, "//input[@name='confirmar']")
        botoes_voltar_paga = driver.find_elements(By.XPATH, "//input[@name='voltar']")

        if len(botoes_confirmar) > 0 and len(botoes_voltar_paga) > 0:
            spanContaPaga = driver.find_element(
                By.XPATH, "//span[contains(normalize-space(), 'já está paga.')]"
            ).text.strip()

            print(f"-> Aviso na Matrícula {matricula} ({texto_link}): {spanContaPaga}. Confirmando para retificar...")
            conta_estava_paga = True

            botoes_confirmar[0].click()
            time.sleep(0.5)

        # 4. Seleciona Motivo da Retificação
        retificacao_select = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//select[@name='motivoRetificacaoID']"))
        )
        Select(retificacao_select).select_by_value("55")

        # 4.1. Verifica se o campo Situação de Esgoto é LIGADO (3) e Volume é 0
        esgotoVolume = driver.find_element(By.XPATH, "//input[@name='consumoEsgoto']")
        esgotoSituacao = driver.find_element(By.XPATH, "//select[@name='situacaoEsgotoConta']")

        valor_volume = esgotoVolume.get_attribute("value").strip()
        select_esgoto = Select(esgotoSituacao)
        situacao_atual = select_esgoto.first_selected_option.get_attribute("value")

        if valor_volume in ("0", "") and situacao_atual == "3":
            select_esgoto.select_by_value("1")
            time.sleep(0.5)

        # 4.2. Preenche campo de observação
        texto_observacao = "Inserir créditos para fins de baixa de fatura. Faturas entregues com valor a menor devido a dedução indevida de impostos, erro ISC MGSetel.Autorizado por Ger. Faturamento e Arrecadaçao, email 17/09/2026."
        campo = driver.find_element(By.XPATH, "//textarea[@name='observacao']")
        campo.clear()
        campo.send_keys(texto_observacao)

        # 5. Salva janela principal e abre o Pop-up de Créditos
        janela_principal = driver.current_window_handle
        
        time.sleep(0.5)
        add_Credito_Realizados = driver.find_element(By. XPATH, value = "//body[1]/div[1]/form[1]/table[3]/tbody[1]/tr[1]/td[2]/table[3]/tbody[1]/tr[18]/td[1]/table[1]/tbody[1]/tr[1]/td[2]/input[1]")
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", add_Credito_Realizados)

        WebDriverWait(driver, 15).until(EC.number_of_windows_to_be(2))

        for handle in driver.window_handles:
            if handle != janela_principal:
                driver.switch_to.window(handle)
                break

        # 6. Preenche os dados na janela Pop-up
        tipoCredito_select = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//select[@name='creditoTipoID']"))
        )
        Select(tipoCredito_select).select_by_value("11")

        mesAnoLimpo = texto_link.replace("/", "")

        driver.find_element(By.XPATH, "//input[@name='mesAnoCredito']").send_keys(mesAnoLimpo)
        driver.find_element(By.XPATH, "//input[@name='mesAnoCobranca']").send_keys(mesAnoLimpo)

        valor_credito = valor_bruto.removeprefix("R$").strip()
        campo_valor = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@name='valorCredito']"))
        )
        time.sleep(0.5)
        campo_valor.clear()
        campo_valor.send_keys(valor_credito)

        creditoOrigem_select = driver.find_element(By.XPATH, "//select[@name='creditoOrigemID']")
        Select(creditoOrigem_select).select_by_value("6")

        # Clica em Inserir na janela Pop-up
        driver.find_element(By.XPATH, "//input[@value='Inserir']").click()
        time.sleep(0.8)  # Aguarda o sistema processar ou fechar o pop-up

        # Verifica se a janela secundária ainda está aberta
        if len(driver.window_handles) > 1:
            spans_duplicado = driver.find_elements(
                By.XPATH, "//span[contains(text(),'Tipo de Débito/Crédito selecionado já foi informad')]"
            )
            if len(spans_duplicado) > 0:
                print(f"-> Aviso no Pop-up ({matricula}): Crédito já informado anteriormente. Fechando pop-up...")
            
            # Força o fechamento da janela secundária
            driver.close()

        # Retorna o foco para a janela principal e segue o programa normalmente
        driver.switch_to.window(janela_principal)


        # 7. Clica em Retificar e aceita o alerta
        time.sleep(0.5)
        button_retificar = driver.find_element(By.XPATH, "//input[@id='botaoRetificar']")
        time.sleep(0.5)
        button_retificar.click()

    # Aceita o primeiro alerta (Data de vencimento anterior à data corrente)
        dataVencimentoAnteriorDataCorrente = WebDriverWait(driver, 15).until(EC.alert_is_present())
        dataVencimentoAnteriorDataCorrente.accept()

        # Verifica se aparece um SEGUNDO alerta em até 2 segundos e o CANCELA (.dismiss())
        try:
            segundo_alerta = WebDriverWait(driver, 2).until(EC.alert_is_present())
            print(f"-> Segundo alerta detectado ({segundo_alerta.text}). Cancelando...")
            segundo_alerta.dismiss()
        except TimeoutException:
            # Se não aparecer um segundo alerta dentro de 2 segundos, segue o fluxo normalmente
            pass

                # Aguarda a página de resposta carregar completamente (Sucesso, botaoVoltar ou botaoBack)
        WebDriverWait(driver, 20).until(
            EC.any_of(
                EC.presence_of_element_located((By.XPATH, "//input[@name='botaoVoltar']")),
                EC.presence_of_element_located((By.XPATH, '//*[@id="botaoBack"]/input')),
                EC.presence_of_element_located((By.XPATH, "//strong[normalize-space()='Realizar outra Manutençao de Conta']"))
            )
        )

        # 7.1.A Verifica o erro específico de conta negativa (usa //input[@name='botaoVoltar'])
        spans_negativo = driver.find_elements(
            By.XPATH, "//span[normalize-space()='Valor total da conta não pode ser negativo.']"
        )

        if len(spans_negativo) > 0:
            status = spans_negativo[0].text.strip()

            print(f"-> Erro após retificar Matrícula {matricula}: {status}. Registrando e pulando...")
            registrar_status(matricula, referencia, valor_bruto, status)

            botao_voltar = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@name='botaoVoltar']"))
            )
            botao_voltar.click()
            time.sleep(0.5)
            driver.get(manter_conta)
            time.sleep(0.5)
            continue

        # 7.1.B Verifica outros erros/bloqueios que exibem o botaoBack (//*[@id="botaoBack"]/input)
        botoes_back = driver.find_elements(By.XPATH, '//*[@id="botaoBack"]/input')

        if len(botoes_back) > 0 and botoes_back[0].is_displayed():
            mensagem_erro = driver.find_element(
                By.XPATH, '/html/body/table/tbody/tr/td/table[3]/tbody/tr[1]/td[2]/span'
            ).text.strip()

            print(f"-> Erro após retificar Matrícula {matricula}: {mensagem_erro}. Registrando e pulando...")
            registrar_status(matricula, referencia, valor_bruto, mensagem_erro)

            botoes_back[0].click()
            time.sleep(0.5)
            driver.get(manter_conta)
            time.sleep(0.5)
            continue


        # 7.2. Registra no CSV que a matrícula foi retificada com sucesso
        time.sleep(0.5)
        status_final = "Matrícula Retificada" if conta_estava_paga else "Retificada com Sucesso"
        time.sleep(0.5)
        print(f"-> Matrícula {matricula} ({texto_link}): {status_final}")
        time.sleep(0.5)
        registrar_status(matricula, referencia, valor_bruto, status_final)
        
        # 8. GATILHO DO LOOP: Clica em "Realizar outra Manutençao de Conta"
        time.sleep(0.5)
        botton_novoImovel = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//strong[normalize-space()='Realizar outra Manutençao de Conta']"))
        )
        botton_novoImovel.click()
        time.sleep(0.5)

print("Processamento finalizado!")
