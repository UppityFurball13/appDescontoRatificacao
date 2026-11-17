from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
# from selenium.common.exceptions import TimeoutException
import time, csv
#import pandas as pd
#from datetime import datetime
#import locale

# Configura as opções do Chrome
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)

# Inicializa o navegador com as opções
driver = webdriver.Chrome(options=chrome_options)

# Abre o site desejado
driver.get("https://www.google.com")
username = "JOAOYURI"
password = "J9874@"
login_url = "http://10.39.192.79:8080/gsan/efetuarLoginAction.do"
manter_conta = "http://10.39.192.79:8080/gsan/exibirManterContaAction.do?menu=sim"
driver.get(login_url)

username_field = driver.find_element(By.XPATH, value = "//input[@name='login']")
password_field = driver.find_element(By.XPATH, value = "//input[@name='senha']")

username_field.send_keys(username)
password_field.send_keys(password)

# "//input[@name='buttonLogin']"
login_button = driver.find_element(By.XPATH, value="//input[@name='buttonLogin']")
login_button.click()
time.sleep(0.3)
driver.get(manter_conta)


meses = {
    "jan": 1, "fev": 2, "mar": 3, "abr": 4,
    "mai": 5, "jun": 6, "jul": 7, "ago": 8,
    "set": 9, "out": 10, "nov": 11, "dez": 12,
}

# guia de coluna
# ['Matrícula' == 0, 'Referência'  == 1, 'Diferença de imposto'  == 2]


# r == para leitura; w == para escrita; a = para atualizar
with open('./NewTextDocument.csv', 'r', encoding='utf-8') as archive:
  csv_writer = csv.reader(archive, delimiter=',')
  # pula a primeira linha do arquivo
  next(archive)
  # será que da pra colocar o dado de uma coluna em uma varaivel? sim, da
  for collun in csv_writer: 
    matricula_key = collun[0]
    # o valor da variavel é colocado no input
    matricula_field = driver.find_element(By. XPATH, value="//input[@name='idImovel']")
    matricula_field.send_keys(matricula_key, Keys.RETURN)
   
    # mes_abreviado em mes_numero e click no elemento após comparação
    data_referencia = collun[1]
    mes_abreviado, ano = data_referencia.split("/", 1)
    mes_numero = meses[mes_abreviado.strip().lower().rstrip(".")]
    texto_link = f"{mes_numero:02d}/{ano.strip()}"
    xpathA = f"//a[normalize-space(.)='{texto_link}']"
    botton_idImovel = driver.find_element(By. XPATH, value=xpathA)
    time.sleep(1)
    botton_idImovel.click()

    #select Motivo da Retificação
    # 1. Localizar o elemento <select>
    time.sleep(0.3)
    retificacao_select = driver.find_element(By.XPATH, value="//select[@name='motivoRetificacaoID']")

    # 2. Criar o objeto Select
    time.sleep(0.3)
    selectRetificacao = Select(retificacao_select)
    time.sleep(0.3)

    # 3. Selecionar uma opção (escolha uma das formas abaixo):

    # Opção B: Pelo atributo 'value' da tag <option>
    selectRetificacao.select_by_value("55")

    # campo de obeservação
    #campo = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(By.XPATH, value = "//textarea[@name='observacao']"))
    texto_observacao = "Inserir créditos para fins de baixa de fatura. Faturas entregues com valor a menor devido a dedução indevida de impostos, erro ISC MGSetel.Autorizado por Ger. Faturamento e Arrecadaçao, email 17/09/2026."
    campo = driver.find_element(By.XPATH, value="//textarea[@name='observacao']")
    campo.send_keys(texto_observacao)

    #botton_idImovel = driver.find_element(By. XPATH, value=)
    time.sleep(1)

    # A OUTRA JANELA
    # 1. Salvar o identificador (handle) da janela principal
    janela_principal = driver.current_window_handle

    # 2. Realizar a ação que abre a nova janela/pop-up
    add_Credito_Realizados = driver.find_element(By.XPATH, value = "//body[1]/div[1]/form[1]/table[3]/tbody[1]/tr[1]/td[2]/table[3]/tbody[1]/tr[18]/td[1]/table[1]/tbody[1]/tr[1]/td[2]/input[1]")
    add_Credito_Realizados.click()


    # 3. Esperar até que o navegador tenha exatamente 2 janelas abertas
    WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))

    # 4. Encontrar o ID da nova janela e mudar o foco para ela
    for handle in driver.window_handles:
        if handle != janela_principal:
            driver.switch_to.window(handle)
            break

    # ==========================================================
    # 5. FAZER O QUE TIVER QUE FAZER NA NOVA JANELA AQUI
    # Seleciona o tipo de Crédito: 
    # "//select[@name='creditoTipoID']"
    tipoCredito_select = driver.find_element(By.XPATH, value="//select[@name='creditoTipoID']")
    selectCredito = Select(tipoCredito_select)
    # "//option[@value='11'] == ACERTO ARRECADACAO"
    selectCredito.select_by_value("11")

    # tratamento de mm/aaaa para mmaaaa
    mesAnoLimpo = texto_link.replace("/", "")

    # colocar o valor de Data usado antes pra esses
    mesAnoCredito = driver.find_element(By. XPATH, value="//input[@name='mesAnoCredito']")
    mesAnoCredito.send_keys(mesAnoLimpo)
    time.sleep(1)
    mesAnoCobranca = driver.find_element(By. XPATH, value="//input[@name='mesAnoCobranca']")
    mesAnoCobranca.send_keys(mesAnoLimpo)
    time.sleep(1)

    # colocar o Valor de Credito
    valor_credito = collun[2].strip().removeprefix("R$").strip()
    campo_valor = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//input[@name='valorCredito']")))
    campo_valor.clear()
    campo_valor.send_keys(valor_credito)

    # seleciona Descontos Concedidos no menu Select
    creditoOrigem_select = driver.find_element(By.XPATH, value="//select[@name='creditoOrigemID']")
    selectOrigem = Select(creditoOrigem_select)
    # "//option[@value='6']" == DESCONTOS CONCEDIDOS
    selectOrigem.select_by_value("6")
    # clcika em Inserir e troca pra tela principal
    button_inserir = driver.find_element(By.XPATH, value="//input[@value='Inserir']")
    button_inserir.click()
    # 6. Fechar a janela secundária (opcional - use apenas se ela não fechar sozinha após a ação)
    #driver.close()
    # 7. Voltar o foco obrigatoriamente para a janela principal
    driver.switch_to.window(janela_principal)


    button_retificar = driver.find_element(By.XPATH, value="//input[@id='botaoRetificar']")
    button_retificar.click()

    dataVencimentoAnteriorDataCorrente = WebDriverWait(driver, 10).until(EC.alert_is_present())
    dataVencimentoAnteriorDataCorrente.accept()

    time.sleep(2)

    botton_novoImovel = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//strong[normalize-space()='Realizar outra Manutençao de Conta']")))

    botton_novoImovel.click()
