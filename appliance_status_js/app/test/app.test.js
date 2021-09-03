import {expect} from "chai";
import { extendButtonBehavior, extendFormBehavior } from "../src/app";
import * as jQuery from "jquery-jsdom";

describe("extendButtonBehavior", function(){
    it("disables the button", function(){
        const jq = jQuery("<form><button></form>");
        const button = jq.find('button');
        const form = jq.find('form');
        expect(extendButtonBehavior(button, form).attr('disabled')).to.equal("disabled");


    })
})
