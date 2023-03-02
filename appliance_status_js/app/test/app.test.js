import {expect} from "chai";
import { extendButtonBehavior, extendFormBehavior } from "../src/app";

const jsdom = require("jsdom");
const { JSDOM } = jsdom;

describe("extendButtonBehavior", function(){
    it("disables the button", function(){
        const doc = new JSDOM("<div><form><button/></form></div>").window.document;
        const button = doc.querySelector('button');
        const form = doc.querySelector('form');
        expect(extendButtonBehavior(button, form).getAttribute('disabled')).to.equal("disabled");
    });
    it("reenables the button upon change", function(){
        const dom = new JSDOM("<div><form><button/></form></div>");
        const doc = dom.window.document;
        const button = doc.querySelector('button');
        const form = doc.querySelector('form');
        extendButtonBehavior(button, form);
        button.dispatchEvent(new dom.window.Event("change", {bubbles: true}));
        expect(button.getAttribute('disabled')).to.equal(null);
    })
})

describe("extendFormBehavior", function(){
    it("does things that are unreasonable to test in nodejs", function(){
        // I see the light now. No more jquery. 
    });
})
