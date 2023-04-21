project_name: "covid-extension"

application: custom-extension-js {
  label: "Covid Extension (JavaScript)"
  url: "https://localhost:8080/bundle.js"
  entitlements: {
    use_iframes: yes
    use_embeds: yes
    core_api_methods: ["run_inline_query"]
  }
}
