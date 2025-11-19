# k8s-config-generator

## Overview

`k8s-config-generator` is a Python script that generates Kubernetes configuration files for a specified number of teams. The generated files include namespaces, roles, role bindings, quotas, and client certificates. The script takes command-line arguments to configure the generated files.

## Pour commencer

1. Clonez ce dépôt sur votre machine locale :

    ```bash
    git clone https://github.com/<username>/k8s-config-generator.git
    ```

2. Créez et activez un environnement virtuel :

    ```bash
    python -m venv .env && source .env/bin/activate
    ```

3. Installez les dépendances requises :

    ```bash
    pip install -r requirements.txt
    ```

## Usage

Déplacez-vous dans le répertoire principal de ce projet, puis exécutez la commande suivante :

```bash
 kubectl config view >> kubeconfig.yaml
```

Exécutez ensuite :

```bash
cd src && python main2.py
```

Vous pouvez conserver les valeurs par défaut en appuyant sur Entrée pour chaque option, depuis --kubeconfig_path jusqu’à la dernière.

Les arguments de la ligne de commande sont les suivants :

- `--out_directory`: The directory where the generated files will be saved.
- `--group`: The group number.
- `--team`: The team number.
- `--kubeconfig_path`: The path to the kubeconfig file.
- `--cpu_limit`: The CPU limit for the quota.
- `--memory_limit`: The memory limit for the quota.
- `--cpu_request`: The CPU request for the quota.
- `--memory_request`: The memory request for the quota.
- `--role_resources`: The resources that the role will have access to.
- `--verbs`: The verbs that the role will have access to.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
