stage('Terraform Format Check') {
    steps {
        sh 'cd terraform && terraform fmt -check'
    }
}

stage('Terraform Init') {
    steps {
        sh 'cd terraform && terraform init'
    }
}

stage('Terraform Validate') {
    steps {
        sh 'cd terraform && terraform validate'
    }
}
