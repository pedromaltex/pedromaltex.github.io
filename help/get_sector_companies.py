from yahooquery import Screener

'''screener = Screener()
print(screener.available_screeners)'''


def get_companiesbysector(sector): # Obtém 100 maiores empresas do determinado setor
    sector_indices = [
    'ms_basic_materials',
    'ms_communication_services',
    'ms_consumer_cyclical',
    'ms_consumer_defensive',
    'ms_energy',
    'ms_financial_services',
    'ms_healthcare',
    'ms_industrials',
    'ms_real_estate',
    'ms_technology',
    'ms_utilities',
    'most_visited_basic_materials',
    'most_visited_communication_services',
    'most_visited_consumer_cyclical',
    'most_visited_consumer_defensive',
    'most_visited_energy',
    'most_visited_financial_services',
    'most_visited_healthcare',
    'most_visited_industrials',
    'most_visited_real_estate',
    'most_visited_technology',
    'most_visited_utilities'
]

        
    # Obtém as empresas do setor escolhido
    screener = Screener()
    data = screener.get_screeners(sector, count=100)  # Pode ajustar 'count'

    #print(data[sector]['quotes'][0]['symbol'])

    # Extraindo os símbolos das empresas
    sector_tickers = [stock['symbol'] for stock in data[f'ms_{sector}']['quotes']]
    return sector_tickers

get_companiesbysector('technology')