#system libraries
import time

class thread_timer:

    #RESUMO: testa um função e retorna o tempo de execução da mesma
    #no caso da função com parâmetros deve-se definir até os parâmetros opcionais
    #target_function é a função 'sem call/chamar'
    #params é um tupple/tupla
    def TestFunction(target_function, params):
        start_time = time.perf_counter()
        function_return = target_function(*params)
        finish_time = time.perf_counter()
        print("tempo total da função '" + target_function.__name__ + "' = " + str(round(finish_time - start_time, 4)) + " segundos")
        print("resultado da função = " + str(function_return))
        