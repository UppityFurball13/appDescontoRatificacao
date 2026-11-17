from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
import time, csv

# Configura as opções do Chrome
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)

# Inicializa o navegador com as opções
driver = webdriver.Chrome(options=chrome_options)

# Faz login no GSAN
username = "JOAOYURI"
password = "J9874@"
login_url = "http://10.39.192.79:8080/gsan/efetuarLoginAction.do"
manter_conta = "http://10.39.192.79:8080/gsan/exibirManterContaAction.do?menu=sim"
driver.get(login_url)

driver.find_element(By.XPATH, "//input[@name='login']").send_keys(username)
driver.find_element(By.XPATH, "//input[@name='senha']").send_keys(password)
driver.find_element(By.XPATH, "//input[@name='buttonLogin']").click()

time.sleep(0.3)
driver.get(manter_conta)

meses = {
    "jan": 1, "fev": 2, "mar": 3, "abr": 4,
    "mai": 5, "jun": 6, "jul": 7, "ago": 8,
    "set": 9, "out": 10, "nov": 11, "dez": 12,
}

# ==============================================================================
# LOOP AUTOMÁTICO PELAS LINHAS DO CSV
# ==============================================================================
with open('./milMatriculasParaRetificar.csv', 'r', encoding='utf-8') as archive:
    csv_reader = csv.reader(archive, delimiter=',')
    next(csv_reader)  # Pula o cabeçalho

    for numero_linha, collun in enumerate(csv_reader, start=2):
        # Ignora linhas vazias ou sem matrícula na primeira coluna
        if len(collun) < 3 or not collun[0].strip():
            continue

        matricula = collun[0].strip()
        referencia = collun[1].strip()
        valor_bruto = collun[2].strip()

        print(f"Processando linha {numero_linha} | Matrícula: {matricula} | Ref: {referencia}")

        # 1. Aguarda o campo de matrícula estar pronto
        matricula_field = driver.find_element(By. XPATH, value="//input[@name='idImovel']")
        time.sleep(0.7)
        matricula_field.clear()
        time.sleep(0.7)
        matricula_field.send_keys(matricula, Keys.RETURN)

        # 2. Converte mês abreviado e clica na referência da conta
        mes_abreviado, ano = referencia.split("/", 1)
        mes_numero = meses[mes_abreviado.strip().lower().rstrip(".")]
        texto_link = f"{mes_numero:02d}/{ano.strip()}"
        xpathA = f"//a[normalize-space(.)='{texto_link}']"

        time.sleep(0.7)
        botton_idImovel = driver.find_element(By. XPATH, value=xpathA)
        time.sleep(0.7)
        botton_idImovel.click()

        # 3. Seleciona Motivo da Retificação
        time.sleep(0.7)
        retificacao_select = driver.find_element(By.XPATH, value="//select[@name='motivoRetificacaoID']")
        time.sleep(0.7)
        Select(retificacao_select).select_by_value("55")

        # 4. Preenche campo de observação
        texto_observacao = "Inserir créditos para fins de baixa de fatura. Faturas entregues com valor a menor devido a dedução indevida de impostos, erro ISC MGSetel.Autorizado por Ger. Faturamento e Arrecadaçao, email 17/09/2026."
        time.sleep(0.7)
        campo = driver.find_element(By.XPATH, "//textarea[@name='observacao']")
        campo.clear()
        campo.send_keys(texto_observacao)
        time.sleep(0.7)

        # 5. Salva janela principal e abre o Pop-up de Créditos
        janela_principal = driver.current_window_handle

        add_Credito_Realizados = driver.find_element(By.XPATH, "//body[1]/div[1]/form[1]/table[3]/tbody[1]/tr[1]/td[2]/table[3]/tbody[1]/tr[18]/td[1]/table[1]/tbody[1]/tr[1]/td[2]/input[1]")
        add_Credito_Realizados.click()
        
        time.sleep(0.7)
        WebDriverWait(driver, 15).until(EC.number_of_windows_to_be(2))

        for handle in driver.window_handles:
            if handle != janela_principal:
                driver.switch_to.window(handle)
                break

        # 6. Preenche os dados na janela Pop-up
        tipoCredito_select = driver.find_element(By. XPATH, value= "//select[@name='creditoTipoID']")
        time.sleep(0.7)
        Select(tipoCredito_select).select_by_value("11")

        # Retira a barra de mm/aaaa -> mmaaaa
        mesAnoLimpo = texto_link.replace("/", "")

        driver.find_element(By.XPATH, "//input[@name='mesAnoCredito']").send_keys(mesAnoLimpo)
        driver.find_element(By.XPATH, "//input[@name='mesAnoCobranca']").send_keys(mesAnoLimpo)
        time.sleep(0.7)
        
        valor_credito = valor_bruto.removeprefix("R$").strip()

        campo_valor = driver.find_element(By. XPATH, value= "//input[@name='valorCredito']")
        time.sleep(0.7)
        campo_valor.clear()
        campo_valor.send_keys(valor_credito)
        time.sleep(0.7)

        creditoOrigem_select = driver.find_element(By.XPATH, "//select[@name='creditoOrigemID']")
        Select(creditoOrigem_select).select_by_value("6")

        # Clica em Inserir e retorna o foco para a janela principal
        driver.find_element(By.XPATH, "//input[@value='Inserir']").click()
        driver.switch_to.window(janela_principal)

        # 7. Clica em Retificar e aceita o alerta
        # button_retificar = driver.find_element(By. XPATH,  value="//input[@id='botaoRetificar']")
        time.sleep(0.7)
        button_retificar = driver.find_element(By. XPATH, value="//input[@id='botaoRetificar']")
        time.sleep(0.7)
        button_retificar.click()

        dataVencimentoAnteriorDataCorrente = WebDriverWait(driver, 15).until(EC.alert_is_present())
        time.sleep(0.7)
        dataVencimentoAnteriorDataCorrente.accept()

        # 8. GATILHO DO LOOP: Clica em "Realizar outra Manutençao de Conta"
        time.sleep(1)
        botton_novoImovel = driver.find_element(By. XPATH, value="//strong[normalize-space()='Realizar outra Manutençao de Conta']")
        time.sleep(1.2)
        
        botton_novoImovel.click()

print("Todas as matrículas do CSV foram processadas com sucesso!")
