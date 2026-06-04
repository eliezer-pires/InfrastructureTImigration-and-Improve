#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de Automação para Mascaramento de Configurações Cisco IOS.
Este script realiza a análise e substituição consistente de informações sensíveis
(Endereços IP, nomes de domínio, comunidades SNMP e usuários locais) por dados fictícios.
"""

import os
import re
import shutil

# Diretórios
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(CONFIG_DIR, "backups")

# Lista de máscaras de sub-rede comuns e wildcards que devem ser preservadas
COMMON_MASKS = {
    # Máscaras de sub-rede
    "255.255.255.255", "255.255.255.254", "255.255.255.252", "255.255.255.248",
    "255.255.255.240", "255.255.255.224", "255.255.255.192", "255.255.255.128",
    "255.255.255.0", "255.255.254.0", "255.255.252.0", "255.255.248.0",
    "255.255.240.0", "255.255.224.0", "255.255.192.0", "255.255.128.0",
    "255.255.0.0", "255.254.0.0", "255.248.0.0", "255.240.0.0", "255.224.0.0",
    "255.192.0.0", "255.128.0.0", "255.0.0.0", "0.0.0.0",
    # Máscaras Curinga (Wildcard masks)
    "0.0.0.255", "0.0.0.127", "0.0.0.63", "0.0.0.31", "0.0.0.15", "0.0.0.7",
    "0.0.0.3", "0.0.0.1", "0.0.1.255", "0.0.3.255", "0.0.7.255", "0.0.15.255",
    "0.0.31.255", "0.0.255.255", "0.255.255.255"
}

# Mapeamento predefinido de prefixos /24 para manter a estrutura e coerência lógica
PREFIX_MAP = {
    "10.116.36": "10.99.36",
    "10.116.38": "10.99.38",
    "10.252.200": "10.99.200",
    "10.253.200": "10.99.201",
    "150.0.3": "10.99.3",
    "192.168.36": "10.99.136",
    "192.168.37": "10.99.137",
    "192.168.38": "10.99.138",
    "192.168.200": "10.99.150",
    "192.168.252": "10.99.151"
}

# Mapeamento dinâmico para novos prefixos descobertos
dynamic_prefix_map = {}
dynamic_prefix_counter = 160

# Mapeamento de usuários administradores para nomes fictícios
USER_MAP = {
    "manutzagal": "admin_principal",
    "demeloembp": "admin_eliezer",
    "queirozgqs": "admin_backup",
    "romulorab": "admin_romulo",
    "munizcms": "admin_muniz",
    "otavioogsn": "admin_otavio",
    "zagalzinho": "admin_auxiliar",
    "zagal": "admin_zagal"
}

# Mapeamento de comunidades SNMP
SNMP_MAP = {
    "51GCC": "snmp_public_ro",
    "mrtg2011tmrj": "snmp_mrtg_ro",
    "netflow": "snmp_netflow_ro",
    "Gerencia%CGTEC": "snmp_gerencia_ro",
    "GCC": "snmp_gcc_ro"
}

# Mapeamento geral de traduções de IP realizadas para fins de relatório
ip_translations = {}

def get_masked_ip(ip):
    """Retorna um IP fictício mantendo consistência e coerência lógica."""
    if ip in COMMON_MASKS:
        return ip
    
    if ip in ip_translations:
        return ip_translations[ip]
    
    parts = ip.split('.')
    if len(parts) != 4:
        return ip
        
    prefix = '.'.join(parts[:3])
    last_octet = parts[3]
    
    if prefix in PREFIX_MAP:
        new_prefix = PREFIX_MAP[prefix]
    else:
        global dynamic_prefix_counter
        if prefix not in dynamic_prefix_map:
            dynamic_prefix_map[prefix] = f"10.99.{dynamic_prefix_counter}"
            dynamic_prefix_counter += 1
        new_prefix = dynamic_prefix_map[prefix]
        
    masked_ip = f"{new_prefix}.{last_octet}"
    ip_translations[ip] = masked_ip
    return masked_ip

def mask_line(line):
    """Aplica todas as regras de mascaramento a uma única linha de configuração."""
    # 1. Substituir Endereços IP (Regex para bater em X.X.X.X)
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    line = re.sub(ip_pattern, lambda m: get_masked_ip(m.group(0)), line)
    
    # 2. Substituir domínios (51gcc.intraer -> empresa.ficticia)
    line = re.sub(r'51gcc\.intraer', 'empresa.ficticia', line, flags=re.IGNORECASE)
    
    # 3. Substituir VTP Domain (zagal -> vtp-ficticio)
    line = re.sub(r'\bvtp domain zagal\b', 'vtp domain vtp-ficticio', line, flags=re.IGNORECASE)
    
    # 4. Substituir Usuários na linha de configuração
    # Ex: username manutzagal privilege 15 ... -> username admin_principal privilege 15 ...
    for user_real, user_fake in USER_MAP.items():
        # Substituição em comandos 'username'
        line = re.sub(rf'\busername\s+{user_real}\b', f'username {user_fake}', line, flags=re.IGNORECASE)
        # Substituição no comentário do cabeçalho 'by username'
        line = re.sub(rf'\bby\s+{user_real}\b', f'by {user_fake}', line, flags=re.IGNORECASE)
        
    # 5. Substituir Comunidades SNMP
    # Ex: snmp-server community 51GCC RO -> snmp-server community snmp_public_ro RO
    for snmp_real, snmp_fake in SNMP_MAP.items():
        line = re.sub(rf'\bsnmp-server community\s+{re.escape(snmp_real)}\b', f'snmp-server community {snmp_fake}', line, flags=re.IGNORECASE)
        
    return line

def main():
    print("=== INICIANDO PROCESSO DE MASCARAMENTO CISCO IOS ===")
    
    # Criar pasta de backups se não existir
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        print(f"Pasta de backups criada em: {BACKUP_DIR}")
        
    # Listar todos os arquivos .cfg
    files = [f for f in os.listdir(CONFIG_DIR) if f.endswith('.cfg')]
    print(f"Total de arquivos .cfg encontrados: {len(files)}")
    
    # Primeiro, fazer backup de todos
    for file in files:
        src = os.path.join(CONFIG_DIR, file)
        dst = os.path.join(BACKUP_DIR, file)
        shutil.copy2(src, dst)
    print("Backups de todos os arquivos gerados com sucesso!")
    
    # Processar cada arquivo
    processed_count = 0
    for file in files:
        filepath = os.path.join(CONFIG_DIR, file)
        
        # Ler conteúdo original
        with open(filepath, 'r', encoding='latin-1') as f:
            content_lines = f.readlines()
            
        # Mascarar conteúdo
        masked_lines = [mask_line(line) for line in content_lines]
        
        # Salvar conteúdo mascarado de volta
        with open(filepath, 'w', encoding='latin-1') as f:
            f.writelines(masked_lines)
            
        processed_count += 1
        print(f"Processado: {file}")
        
    print("\n=== MASCARAMENTO CONCLUÍDO COM SUCESSO! ===")
    print(f"Total de arquivos alterados: {processed_count}")
    
    # Exibir resumo das traduções de IPs
    print(f"\nTotal de IPs reais mascarados de forma consistente: {len(ip_translations)}")
    print("-" * 50)
    print(f"{'IP Real':<20} -> {'IP Fictício':<20}")
    print("-" * 50)
    for real, fake in sorted(ip_translations.items(), key=lambda x: [int(d) for d in x[0].split('.')]):
        print(f"{real:<20} -> {fake:<20}")
    print("-" * 50)
    
if __name__ == "__main__":
    main()
