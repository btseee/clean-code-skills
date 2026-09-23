import { Component, OnInit } from "@angular/core";
import { HttpClient } from "@angular/common/http";

@Component({
  selector: "app-orders",
  standalone: true,
  template: `<ul><li *ngFor="let order of orders">{{ order.customer }}</li></ul>`,
})
export class OrdersComponent implements OnInit {
  orders: { id: string; customer: string }[] = [];

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.http.get<{ id: string; customer: string }[]>("/api/orders").subscribe((orders) => {
      this.orders = orders;
    });
  }
}
