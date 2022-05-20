import { Component, OnInit, Input } from '@angular/core';
import { FormGroup, FormControl } from '@angular/forms';
import { ValidationService } from '../../services/validation.service';

@Component({
  selector: 'control-messages',
  template: `
  <div *ngIf="errorMessage !== null">{{errorMessage}}</div>
  `
})
export class ControlMessagesComponent implements OnInit {

  @Input() control: FormControl;
  constructor() { }

  ngOnInit(): void {
  }
  get errorMessage() {
    if(this.control && this.control.errors) {
      for (let propertyName in this.control.errors) {
        if (this.control.errors.hasOwnProperty(propertyName) && this.control.touched) {
          return ValidationService.getValidatorErrorMessage(propertyName, this.control.errors[propertyName]);
        }
      }
   }
    return null;
  }

}
