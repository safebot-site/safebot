from safebot.validations.validate import calculate_cnpj_matriz

# verifica se dado um CNPJ matriz o mesmo CNPJ matriz é retornado
def test_cnpj_matriz():
   cnpj_matriz_input = "45543915000181"

   cnpj_matriz_result = calculate_cnpj_matriz(cnpj_matriz_input)

   assert cnpj_matriz_result == cnpj_matriz_input

# verifica se dado um CNPJ filial o CNPJ matriz é retornado
def test_cnpj_filial():
   cnpj_filial_input = "45543915084695"
   cnpj_matriz_esperado = "45543915000181"

   cnpj_matriz_result = calculate_cnpj_matriz(cnpj_filial_input)

   assert cnpj_matriz_result == cnpj_matriz_esperado