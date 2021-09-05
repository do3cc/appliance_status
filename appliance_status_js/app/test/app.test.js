import {expect} from "chai";
import { extendButtonBehavior, extendFormBehavior } from "../src/app";
import * as jQuery from "jquery-jsdom";

describe("extendButtonBehavior", function(){
    it("disables the button", function(){
        const jq = jQuery("<div><form><button/></form></div>");
        const button = jq.find('button');
        const form = jq.find('form');
        expect(extendButtonBehavior(button, form).attr('disabled')).to.equal("disabled");
    });
    it("reenables the button upon change", function(){
        const jq = jQuery("<div><form><button/></form></div>");
        const button = jq.find('button');
        const form = jq.find('form');
        extendButtonBehavior(button, form);
        button.trigger("change");
        expect(button.attr('disabled')).to.equal(undefined);
    })
})

describe("extendFormBehavior", function(){
    it("does things that are unreasonable to test in nodejs", function(){
        // I see the light now. No more jquery. 
    });
})
