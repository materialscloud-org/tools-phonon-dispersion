# This code is extracted from Henrique Miranda github page:
Web url: https://github.com/henriquemiranda/phononwebsite/tree/devel/phononweb
branch: devel (last commit: 3b95b0fecaf81126aecd5fa5e36e4188d76e02a1)

1. Clone the repo and checkout devel branch:
$ git clone https://github.com/henriquemiranda/phononwebsite/tree/devel/phononweb
$ git checkout devel

2. Compile the code
To compile the code first install rollup with:
$ npm install rollup

After this build the code with:
$ npm run-script build

this will create the build folder (main.js and phononwebsite.js) with required files.

3. Extracted the required files and modified further to remove requireJs dependency
