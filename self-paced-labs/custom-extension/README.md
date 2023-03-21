# Custom Looker Extension (React & JavaScript)

This example demonstrates a bare bones Looker extension using Javascript.

## Getting Started for Development

1. Clone the repo.

   ```
   # cd ~/ Optional, your user directory is usually a good place to git clone to.
   git clone https://github.com/GoogleCloudPlatform/training-data-analyst.git
   ```

2. Navigate (`cd`) to the `custom-extension` directory on your system

   ```
   cd training-data-analyst/self-paced-labs/custom-extension
   ```

3. Install the dependencies with [Yarn](https://yarnpkg.com/).

   ```
   yarn install
   ```

4. Start the development server

   ```
   yarn develop
   ```

   The extension is now running and serving the JavaScript locally at https://localhost:8080/bundle.js.

5. Log in to Looker and create a new project.

   This is found under **Develop** => **Manage LookML Projects** => **New LookML Project**.

   Select "Blank Project" as your "Starting Point". This will create a new project with no files.

   1. The extension folder has a `manifest.lkml` file.

   Either drag & upload this file into your Looker project, or create a `manifest.lkml` with the same content. Change the `id`, `label`, or `url` as needed.

   ```
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
   ```

6. Create a `model` LookML file in your project. The name doesn't matter but the convention is to name it the same as the project— in this case, `covid-extension.model`.

- Add a connection in this model.
- [Configure the model you created](https://docs.looker.com/data-modeling/getting-started/create-projects#configuring_a_model) so that it has access to the selected connection.
  We do this because Looker permissions data access via models— In order to grant / limit access to an extension, it must be associated with a model.

7. Connect the project to Git. This can be done in multiple ways:

- Create a new repository on GitHub or a similar service, and follow the instructions to [connect your project to Git](https://docs.looker.com/data-modeling/getting-started/setting-up-git-connection)
- A simpler but less powerful approach is to set up git with the "Bare" repository option which does not require connecting to an external Git Service.

8. Commit the changes and deploy them to production through the Project UI.

9. Reload the page and click the `Browse` dropdown menu. You will see the extension in the list.

- The extension will load the JavaScript from the `url` provided in the `application` definition. By default, this is https://localhost:8080/bundle.js. If you change the port your server runs on in the package.json, you will need to also update it in the manifest.lkml.
- Refreshing the extension page will bring in any new code changes from the extension template, although some changes will hot reload.

## Deployment

The process above describes how to run the extension for development. Once you're done developing and ready to deploy, the production version of the extension may be deployed as follows:

1. In the extension project directory build the extension by running `yarn build`.
2. Drag and drop the generated `dist/bundle.js` file into the Looker project interface
3. Modify the `manifest.lkml` to use `file` instead of `url`:

   ```
   project_name: "covid-extension"

   application: custom-extension-js {
     label: "Covid Extension (JavaScript)"
     file: "bundle.js"
     entitlements: {
       use_iframes: yes
       use_embeds: yes
       core_api_methods: ["run_inline_query"]
     }
   }
   ```
