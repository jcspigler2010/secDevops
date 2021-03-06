#!/usr/bin/env groovy

import groovy.json.JsonOutput

// def slackNotificationChannel = "#ci_cd_pipelinetesting"

// def notifySlack(text, channel, attachments) {
//     def slackURL = "https://hooks.slack.com/services/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"
//     def jenkinsIcon = 'https://wiki.jenkins-ci.org/download/attachments/2916393/logo.png'
//
//     def payload = JsonOutput.toJson([text: text,
//         channel: "#ci_cd_pipelinetesting",
//         username: "webhookbot",
//         icon_url: jenkinsIcon
//     ])
//
//     sh "curl -X POST --data-urlencode \'payload=${payload}\' ${slackURL}"
// }



node {
   stage('Preparation') {
            checkout scm

            // Setting up environment variables
            echo "setting up variables..."
            env.zone = params.zones
            env.fqdn = params.fqdn
            // env.domain = fqdn.split('.').last(2).join('.')
            env.appName = params.appName
            env.member = params.member

            env.cert = params.certificate
            env.key = params.key

            sh 'echo $cert > $appName.cert'
            sh 'echo $key > $appName.key'

            env.targertURL = params.targetURL
            env.loginURL = params.authenticationURL
            env.method = params.method
            env.app_user = params.username
            env.app_pass = params.password
            env.userNameField = params.userNameField
            env.passwordField = params.passwordField
            env.checkString = params.checkString
            env.dataFormat = params.dataFormat
            env.vulntoolip = params.vulntoolip
            echo "Data Format: $dataFormat"
            echo "Data_Format: ${dataFormat}"

            env.qaIP = params.qaIP
            env.prodIP = params.prodIP

   }

   stage('certificate validation') {
        sh "echo $key > ${env.BUILD_ID}.key.tmp"
        sh "echo $cert > ${env.BUILD_ID}.cert.tmp"

        sh "cat ${env.BUILD_ID}.key.tmp | tr ' ' '\n' | awk '/BEGIN\$/ { printf(\"%s \", \$0); next } 1' | awk '/RSA\$/ { printf(\"%s \", \$0); next } 1' |  awk '/PRIVATE\$/ { printf(\"%s \", \$0); next } 1' | awk '/END\$/ { printf(\"%s \", \$0); next } 1' |  tee -a ${appName}.key"
        sh "cat ${env.BUILD_ID}.cert.tmp | tr ' ' '\n' | awk '/BEGIN\$/ { printf(\"%s \", \$0); next } 1' | awk '/END\$/ { printf(\"%s \", \$0); next } 1' |  tee -a ${appName}.cert"

        // Verify if Key and Certificate modulus match
        def cert_mod = sh (
                script: "openssl x509 -noout -modulus -in ${appName}.cert",
                returnStatus: true
            ) == 0
        def key_mod = sh (
                script: "openssl rsa -noout -modulus -in ${appName}.key",
                returnStatus: true
            ) == 0
        if( "${cert_mod}" != "${key_mod}" ) {
            echo '[FAILURE] Failed to build'
            currentBuild.result = 'FAILURE'
            }
   }


   stage('Build in QA') {
            // Create LB Config
            withCredentials([[$class: 'UsernamePasswordMultiBinding', credentialsId: 'bigips', usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD']]) {
               ansiblePlaybook(
                    installation: 'ansible-2.7.10',
                    colorized: true,
                    inventory: "${env.WORKSPACE}/hosts.ini",
                    playbook: 'importCrypto.yaml',
                    limit: 'qa:&$zone',
                    extras: '-vvv',
                    sudoUser: null,
                    extraVars: [
                        bigip_username: USERNAME,
                        bigip_password: PASSWORD,
                        fqdn: fqdn,
                        appName: appName
                ])
            }

            withCredentials([[$class: 'UsernamePasswordMultiBinding', credentialsId: 'bigips', usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD']]) {
              ansiblePlaybook(
                installation: 'ansible-2.7.10',
                colorized: true,
                inventory: "${env.WORKSPACE}/hosts.ini",
                playbook: 'myVSConfig.yaml',
                limit: 'qa:&$zone',
                extras: '-vvv',
                sudoUser: null,
                extraVars: [
                        bigip_username: USERNAME,
                        bigip_password: PASSWORD,
                        fqdn: fqdn,
                        appName: appName,
                        vsIP: qaIP,
                        member: member
              ])
            }

          withCredentials([[$class: 'UsernamePasswordMultiBinding', credentialsId: 'bigips', usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD']]) {
            ansiblePlaybook(
                installation: 'ansible-2.7.10',
                colorized: true,
                inventory: "${env.WORKSPACE}/hosts.ini",
                playbook: 'createASMPolicy.yaml',
                limit: 'qa:&$zone',
                extras: '-vvv',
                sudoUser: null,
                extraVars: [
                        bigip_username: USERNAME,
                        bigip_password: PASSWORD,
                        fqdn: fqdn,
                        appName: appName
                ])
          }

   }

   stage('QA Tests') {
     input 'Proceed to Intensive tests in QA?'
   }



  stage('Prepare Crawling and DAST') {
        //1. Convert the dataformat line so it can used by wget for crawling
        env.wget_dataFormat = sh (
         script: "echo 'username=%U&password=%P&Login=Login' | sed 's/%U/${app_user}/g' | sed 's/%P/${app_pass}/g'",
         returnStdout: true
         ).trim()

         env.targertURL = params.targetURL
         env.loginURL = params.authenticationURL
         env.method = params.method
         env.app_user = params.username
         env.app_pass = params.password
         env.userNameField = params.userNameField
         env.passwordField = params.passwordField
         env.checkString = params.checkString
         env.dataFormat = params.dataFormat
         env.vulntoolip = params.vulntoolip
         echo "Data Format: $dataFormat"
         echo "Data_Format: ${dataFormat}"

         env.qaIP = params.qaIP

        sh "cat base_dast.w3af >> ${env.BUILD_ID}_dast.w3af"
        sh "echo auth detailed >> ${env.BUILD_ID}_dast.w3af"
        sh "echo auth config detailed >> ${env.BUILD_ID}_dast.w3af"
        sh "echo set username admin >> ${env.BUILD_ID}_dast.w3af"
        sh "echo set password password >> ${env.BUILD_ID}_dast.w3af"
        sh "echo set method POST >> ${env.BUILD_ID}_dast.w3af"
        sh "echo set auth_url http://${env.member}/dvwa/${env.loginURL}>> ${env.BUILD_ID}_dast.w3af"
        sh "echo set username_field ${env.userNameField} >> ${env.BUILD_ID}_dast.w3af"
        sh "echo set password_field ${env.passwordField} >> ${env.BUILD_ID}_dast.w3af"
        sh "echo set check_url http://${env.member}/dvwa/${env.targertURL} >> ${env.BUILD_ID}_dast.w3af"
        sh "echo set check_string 'admin'>> ${env.BUILD_ID}_dast.w3af"
        sh "echo set data_format $dataFormat >> ${env.BUILD_ID}_dast.w3af"
        sh "echo back >> ${env.BUILD_ID}_dast.w3af"
        sh "echo output console, xml_f5asm >> ${env.BUILD_ID}_dast.w3af"
        sh "echo output config xml_f5asm >> ${env.BUILD_ID}_dast.w3af"
        sh "echo set output_file /opt/w3af/jenkins/asm_xml_results/f5_dynamic_waf/${env.BUILD_ID}_dast.xml >> ${env.BUILD_ID}_dast.w3af"
        sh "echo set verbose False >> ${env.BUILD_ID}_dast.w3af"
        sh "echo back >> ${env.BUILD_ID}_dast.w3af"
        sh "echo output config console >> ${env.BUILD_ID}_dast.w3af"
        sh "echo set verbose False >> ${env.BUILD_ID}_dast.w3af"
        sh "echo back >> ${env.BUILD_ID}_dast.w3af"
        sh "echo back >> ${env.BUILD_ID}_dast.w3af"
        sh "echo target >> ${env.BUILD_ID}_dast.w3af"
        sh "echo set target http://${env.member}/dvwa >> ${env.BUILD_ID}_dast.w3af"
        sh "echo back >> ${env.BUILD_ID}_dast.w3af"
        sh "echo cleanup >> ${env.BUILD_ID}_dast.w3af"
        sh "echo start >> ${env.BUILD_ID}_dast.w3af"
        sh "echo exit >> ${env.BUILD_ID}_dast.w3af"
   }

   stage('Crawling & Vulnerability Scan') {
        // Crawling now
        ansiblePlaybook(
          installation: 'ansible-2.7.10',
          credentialsId: 'w3af',
          inventory: "hosts.ini",
          become: true,
          playbook: "w3af_scan.yaml",
          disableHostKeyChecking: true,
          colorized: true,
          limit: 'w3af_servers',
          extraVars: [
                  workspace: "${env.WORKSPACE}",
                  build_id: "${env.BUILD_ID}",
                  vulntoolip: vulntoolip,
                  wget_dataFormat: wget_dataFormat,
                  member: member,
                  targetlogin: targertURL,
                  targeturl: loginURL
          ])
   }


   stage('Import Vulnerabilities') {
        withCredentials([[$class: 'UsernamePasswordMultiBinding', credentialsId: 'bigips', usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD']]) {
            ansiblePlaybook(
                installation: 'ansible-2.7.10',
                colorized: true,
                inventory: "${env.WORKSPACE}/hosts.ini",
                playbook: 'removeASMWildcard.yaml',
                limit: 'qa:&$zone',
                extras: '-vvv',
                sudoUser: null,
                extraVars: [
                    bigip_username: USERNAME,
                    bigip_password: PASSWORD,
                    appName: appName
                ])
             ansiblePlaybook(
                installation: 'ansible-2.7.10',
                colorized: true,
                inventory: "${env.WORKSPACE}/hosts.ini",
                playbook: 'importVulnerabilities.yaml',
                limit: 'qa:&$zone',
                extras: '-vvv',
                sudoUser: null,
                extraVars: [
                    bigip_username: USERNAME,
                    bigip_password: PASSWORD,
                    fqdn: fqdn,
                    appName: appName,
                    buildId: "${env.BUILD_ID}"
            ])
        }
   }

   stage('Move to Production and Approve Vulnerability Test Updates') {
     input 'Approve Vulnerability Test Updates in ASM Policy and Publish Service in Production?'
   }

   stage('Create Service in Production') {

            withCredentials([[$class: 'UsernamePasswordMultiBinding', credentialsId: 'bigips', usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD']]) {

              ansiblePlaybook(
                  installation: 'ansible-2.7.10',
                  colorized: true,
                  inventory: "${env.WORKSPACE}/hosts.ini",
                  playbook: 'exportPolicy.yaml',
                  limit: 'qa:&$zone',
                  extras: '-vvv',
                  sudoUser: null,
                  extraVars: [
                      bigip_username: USERNAME,
                      bigip_password: PASSWORD,
                      fqdn: fqdn,
                      build_id: "${env.BUILD_ID}",
                      appName: appName
                  ])
              ansiblePlaybook(
                  installation: 'ansible-2.7.10',
                  colorized: true,
                  inventory: "${env.WORKSPACE}/hosts.ini",
                  playbook: 'importPolicy.yaml',
                  limit: 'prod:&$zone',
                  extras: '-vvv',
                  sudoUser: null,
                  extraVars: [
                      host: 'prod:&$zone',
                      bigip_username: USERNAME,
                      bigip_password: PASSWORD,
                      fqdn: fqdn,
                      build_id: "${env.BUILD_ID}",
                      appName: appName
                  ])
               ansiblePlaybook(
                    installation: 'ansible-2.7.10',
                    colorized: true,
                    inventory: "${env.WORKSPACE}/hosts.ini",
                    playbook: 'importCrypto.yaml',
                    limit: 'prod:&$zone',
                    extras: '-vvv',
                    sudoUser: null,
                    extraVars: [
                        bigip_username: USERNAME,
                        bigip_password: PASSWORD,
                        fqdn: fqdn,
                        appName: appName
                ])

                ansiblePlaybook(
                    installation: 'ansible-2.7.10',
                    colorized: true,
                    inventory: "${env.WORKSPACE}/hosts.ini",
                    playbook: 'myVSConfig.yaml',
                    limit: 'prod:&$zone',
                    extras: '-vvv',
                    sudoUser: null,
                    extraVars: [
                        bigip_username: USERNAME,
                        bigip_password: PASSWORD,
                        fqdn: fqdn,
                        vsIP: prodIP,
                        appName: appName,
                        member: member
                ])
                ansiblePlaybook(
                    installation: 'ansible-2.7.10',
                    colorized: true,
                    inventory: "${env.WORKSPACE}/hosts.ini",
                    playbook: 'attachASMPolicy.yaml',
                    limit: 'prod:&$zone',
                    extras: '-vvv',
                    sudoUser: null,
                    extraVars: [
                        bigip_username: USERNAME,
                        bigip_password: PASSWORD,
                        appName: appName
                ])
            }
   }

   // stage("Post to Slack") {
   //      notifySlack("A new service is deployed!", slackNotificationChannel, [])
   // }



}
