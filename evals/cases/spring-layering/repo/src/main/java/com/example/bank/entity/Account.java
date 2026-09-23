package com.example.bank.entity;

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.Id;

@Entity
public class Account {

    @Id
    @GeneratedValue
    private Long id;

    private long balanceCents;

    private boolean closed;

    protected Account() {
    }

    public Account(long balanceCents) {
        this.balanceCents = balanceCents;
    }

    public Long getId() {
        return id;
    }

    public long getBalanceCents() {
        return balanceCents;
    }

    public void deposit(long amountCents) {
        this.balanceCents += amountCents;
    }

    public void withdraw(long amountCents) {
        this.balanceCents -= amountCents;
    }

    public boolean isClosed() {
        return closed;
    }
}
