import boto3
import os

def lambda_handler(event, context):
    # Verifica se a flag simulate_down foi passada no evento.
    # Caso não esteja presente, utiliza a variável de ambiente SIMULATE_DOWN.
    simulate_down = event.get("simulate_down", os.environ.get("SIMULATE_DOWN", "false").lower() == "true")
    print(f"Simulate_down: {simulate_down}")
    
    # Cria cliente do Direct Connect na região sa-east-1
    dc_client = boto3.client('directconnect', region_name='sa-east-1')
    
    try:
        # Obtém as conexões do Direct Connect
        response = dc_client.describe_connections()
    except Exception as e:
        print(f"Erro ao descrever conexões do Direct Connect: {e}")
        return {'statusCode': 500, 'body': 'Erro ao obter status do Direct Connect.'}
    
    # Verifica o status da conexão
    connections = response.get('connections', [])
    if not connections:
        print("Nenhuma conexão encontrada. Considerando status como 0.")
        status_value = 0
    else:
        # Utiliza a primeira conexão retornada
        connection = connections[0]
        connection_state = connection.get('connectionState', '').lower()
        print(f"Estado da conexão: {connection_state}")
        # Se o estado for 'down', considera status 0; caso contrário, 1
        status_value = 0 if connection_state == 'down' else 1

    # Se a flag de simulação estiver ativa, forçamos o status para 0
    if simulate_down:
        print("Simulação ativada: forçando o status para 0 (Direct Connect down).")
        status_value = 0

    # Lógica: se status for 0 (down), adiciona as rotas; se for 1 (up), remove as rotas.
    if status_value == 0:
        print("Status é 0 (Direct Connect down). Iniciando adição de rotas.")
        ec2_client = boto3.client('ec2', region_name='us-east-1')
        
        route_table_ids = os.environ.get("ROUTE_TABLE_IDS", "<ROUTE_TABLE_IDS>").split(',')
        dest_cidrs = os.environ.get("DEST_CIDR_BLOCKS", "<DEST_CIDR_BLOCKS>").split(',')
        network_interface_id = os.environ.get("NetworkInterfaceId", "<NETWORK_INTERFACE_ID>")
        
        for idx, rt_id in enumerate(route_table_ids):
            cidr = dest_cidrs[idx] if idx < len(dest_cidrs) else dest_cidrs[0]
            try:
                response = ec2_client.create_route(
                    RouteTableId=rt_id,
                    DestinationCidrBlock=cidr,
                    NetworkInterfaceId=network_interface_id
                )
                print(f"Rota adicionada na tabela {rt_id} para destino {cidr}: {response}")
            except Exception as e:
                print(f"Erro ao adicionar rota na tabela {rt_id}: {e}")
    elif status_value == 1:
        print("Status é 1 (Direct Connect up). Iniciando remoção de rotas.")
        ec2_client = boto3.client('ec2', region_name='us-east-1')
        
        route_table_ids = os.environ.get("ROUTE_TABLE_IDS", "<ROUTE_TABLE_IDS>").split(',')
        dest_cidrs = os.environ.get("DEST_CIDR_BLOCKS", "<DEST_CIDR_BLOCKS>").split(',')
        
        for idx, rt_id in enumerate(route_table_ids):
            cidr = dest_cidrs[idx] if idx < len(dest_cidrs) else dest_cidrs[0]
            try:
                response = ec2_client.delete_route(
                    RouteTableId=rt_id,
                    DestinationCidrBlock=cidr
                )
                print(f"Rota removida na tabela {rt_id} para destino {cidr}: {response}")
            except Exception as e:
                print(f"Erro ao remover rota na tabela {rt_id}: {e}")
    else:
        print("Status desconhecido. Nenhuma ação realizada.")
    
    return {
        'statusCode': 200,
        'body': 'Execução da Lambda concluída.'
    }
