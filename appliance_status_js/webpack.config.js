let glob = require("glob");

let entry = __dirname + "/app/src/page.js";
let outputPath = __dirname + "/dist/";
let devtool = "source-map";
let target = "web";
let externals = {};
if (process.env.TESTBUILD) {
	entry = glob.sync(__dirname + "/app/test/**/*.test.js");
	outputPath = __dirname + "/test-dist/";
	devtool = "source-map";
	target = "node";
	externals = { canvas: "commonjs canvas"};
}

module.exports = {
	entry: entry,
	output: {
		path: outputPath,
	},
	resolve: {
		fallback: {
		}
	},
	externals: externals,
	target: target,
	devtool: devtool
}
  
